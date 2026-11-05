// Testes de fumaça/caracterização da LMS API (ecommerce-api-legacy).
// Caixa-preta via HTTP: sobem `node src/app.js` (banco SQLite em memória, recriado
// a cada execução) e validam o contrato atual. Usa apenas o runner nativo do Node
// (`node --test`), sem dependências adicionais. A ordem dos testes importa, pois
// compartilham o mesmo banco em memória.
const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const net = require('node:net');
const path = require('node:path');
const { spawn } = require('node:child_process');

const PORTA = 3000;
const BASE = `http://127.0.0.1:${PORTA}`;
const RAIZ = path.resolve(__dirname, '..');

let proc;
let saida = '';

function portaEmUso(porta) {
    return new Promise((resolve) => {
        const s = net.connect(porta, '127.0.0.1');
        s.once('connect', () => { s.destroy(); resolve(true); });
        s.once('error', () => resolve(false));
    });
}

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

async function aguardarServidor() {
    const limite = Date.now() + 30000;
    while (Date.now() < limite) {
        if (proc.exitCode !== null) throw new Error(`Aplicação encerrou ao iniciar:\n${saida}`);
        try {
            const r = await fetch(`${BASE}/api/admin/financial-report`);
            if (r.status === 200) return;
        } catch (_) { /* ainda subindo */ }
        await esperar(300);
    }
    throw new Error(`Timeout aguardando a aplicação.\n${saida}`);
}

const checkout = (corpo) => fetch(`${BASE}/api/checkout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(corpo),
});

const relatorio = async () => {
    const r = await fetch(`${BASE}/api/admin/financial-report`);
    assert.equal(r.status, 200);
    const dados = await r.json();
    // A ordem de resposta depende de callbacks assíncronos; ordena para comparar.
    return dados.sort((a, b) => a.course.localeCompare(b.course));
};

describe('LMS API', () => {
    before(async () => {
        if (await portaEmUso(PORTA)) {
            throw new Error(`Porta ${PORTA} já está em uso; encerre o processo e rode novamente.`);
        }
        proc = spawn(process.execPath, ['src/app.js'], { cwd: RAIZ });
        proc.stdout.on('data', (d) => { saida += d; });
        proc.stderr.on('data', (d) => { saida += d; });
        await aguardarServidor();
    });

    after(() => {
        if (proc) proc.kill();
    });

    it('relatório financeiro inicial reflete os seeds', async () => {
        const dados = await relatorio();
        assert.equal(dados.length, 2);
        const [clean, docker] = dados;
        assert.equal(clean.course, 'Clean Architecture');
        assert.equal(clean.revenue, 997);
        assert.deepEqual(clean.students, [{ student: 'Leonan', paid: 997 }]);
        assert.equal(docker.course, 'Docker');
        assert.equal(docker.revenue, 0);
        assert.deepEqual(docker.students, []);
    });

    it('checkout sem campos obrigatórios retorna 400', async () => {
        const r = await checkout({ usr: 'Fulano', eml: 'fulano@teste.com' });
        assert.equal(r.status, 400);
    });

    it('checkout de curso inexistente retorna 404', async () => {
        const r = await checkout({ usr: 'Fulano', eml: 'fulano@teste.com', pwd: '123', c_id: 999, card: '4111222233334444' });
        assert.equal(r.status, 404);
    });

    it('checkout com cartão recusado retorna 400', async () => {
        const r = await checkout({ usr: 'João', eml: 'joao@teste.com', pwd: '123', c_id: 1, card: '5111222233334444' });
        assert.equal(r.status, 400);
        assert.equal(await r.text(), 'Pagamento recusado');
    });

    it('checkout com sucesso cria usuário e matrícula', async () => {
        const r = await checkout({ usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444' });
        assert.equal(r.status, 200);
        const corpo = await r.json();
        assert.equal(corpo.msg, 'Sucesso');
        assert.equal(typeof corpo.enrollment_id, 'number');
    });

    it('relatório financeiro reflete o checkout aprovado', async () => {
        const [clean, docker] = await relatorio();
        assert.equal(clean.revenue, 997);
        assert.equal(docker.revenue, 497);
        assert.deepEqual(docker.students, [{ student: 'Guilherme', paid: 497 }]);
    });

    it('checkout de usuário já existente reutiliza o cadastro', async () => {
        const r = await checkout({ usr: 'Leonan', eml: 'leonan@fullcycle.com.br', pwd: '123', c_id: 2, card: '4111222233334444' });
        assert.equal(r.status, 200);
        const [, docker] = await relatorio();
        assert.equal(docker.revenue, 994);
        assert.equal(docker.students.length, 2);
    });

    it('DELETE /api/users/:id retorna 200', async () => {
        const r = await fetch(`${BASE}/api/users/1`, { method: 'DELETE' });
        assert.equal(r.status, 200);
        assert.match(await r.text(), /deletado/i);
    });
});
