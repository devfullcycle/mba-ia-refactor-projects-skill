const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');

let server;
let db;
let baseUrl;

const ADMIN_HEADERS = {
    Authorization: 'Bearer test-admin-token',
    'Content-Type': 'application/json',
};

before(async () => {
    process.env.NODE_ENV = 'test';
    process.env.PORT = '0';
    process.env.ADMIN_TOKEN = 'test-admin-token';
    process.env.LOG_LEVEL = 'error';

    const { bootstrap } = require('../src/app');
    const booted = await bootstrap();
    server = booted.server;
    db = booted.db;

    if (!server.listening) {
        await new Promise((resolve) => server.once('listening', resolve));
    }
    baseUrl = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
    await new Promise((resolve, reject) => {
        server.close((err) => (err ? reject(err) : resolve()));
    });
    await db.close();
});

async function request(path, options = {}) {
    const response = await fetch(`${baseUrl}${path}`, options);
    const text = await response.text();

    let body = text;
    try {
        body = JSON.parse(text);
    } catch (err) {
        // resposta textual (contrato legado)
    }

    return { status: response.status, body, text };
}

test('GET /api/admin/financial-report sem token retorna 401', async () => {
    const res = await request('/api/admin/financial-report');
    assert.equal(res.status, 401);
});

test('GET /api/admin/financial-report retorna o relatório financeiro', async () => {
    const res = await request('/api/admin/financial-report', { headers: ADMIN_HEADERS });

    assert.equal(res.status, 200);
    assert.deepEqual(res.body, [
        {
            course: 'Clean Architecture',
            revenue: 997,
            students: [{ student: 'Leonan', paid: 997 }],
        },
        {
            course: 'Docker',
            revenue: 0,
            students: [],
        },
    ]);
});

test('POST /api/checkout rejeita payload malformado com 400', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usr: 'Guilherme' }),
    });

    assert.equal(res.status, 400);
    assert.equal(res.body, 'Bad Request');
});

test('POST /api/checkout para novo usuário sem pwd retorna 400', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usr: 'Sem Senha',
            eml: 'sem-senha@teste.com',
            c_id: 1,
            card: '4111222233334444',
        }),
    });

    assert.equal(res.status, 400);
    assert.equal(res.body, 'pwd é obrigatório para novo usuário');
});

test('POST /api/checkout recusa cartão que não inicia em 4', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usr: 'João',
            eml: 'joao@teste.com',
            pwd: '123',
            c_id: 1,
            card: '5111222233334444',
        }),
    });

    assert.equal(res.status, 400);
    assert.equal(res.body, 'Pagamento recusado');
});

test('POST /api/checkout aprova cartão iniciado em 4 e cria matrícula', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usr: 'Guilherme',
            eml: 'gui@fullcycle.com.br',
            pwd: 'senhaforte',
            c_id: 2,
            card: '4111222233334444',
        }),
    });

    assert.equal(res.status, 200);
    assert.equal(res.body.msg, 'Sucesso');
    assert.ok(Number.isInteger(res.body.enrollment_id));
});

test('POST /api/checkout para usuário existente sem pwd retorna 401 (SEC-04)', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usr: 'Invasor',
            eml: 'gui@fullcycle.com.br',
            c_id: 2,
            card: '4111222233334444',
        }),
    });

    assert.equal(res.status, 401);
    assert.equal(res.body, 'Credenciais inválidas');
});

test('POST /api/checkout para usuário existente com pwd incorreta retorna 401 (SEC-04)', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usr: 'Invasor',
            eml: 'gui@fullcycle.com.br',
            pwd: 'senha-errada',
            c_id: 2,
            card: '4111222233334444',
        }),
    });

    assert.equal(res.status, 401);
    assert.equal(res.body, 'Credenciais inválidas');
});

test('GET /api/admin/financial-report reflete novo checkout', async () => {
    const res = await request('/api/admin/financial-report', { headers: ADMIN_HEADERS });
    const docker = res.body.find((item) => item.course === 'Docker');

    assert.equal(res.status, 200);
    assert.equal(docker.revenue, 497);
    assert.deepEqual(docker.students, [{ student: 'Guilherme', paid: 497 }]);
});

test('POST /api/checkout retorna 404 para curso inexistente', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usr: 'Guilherme',
            eml: 'gui@fullcycle.com.br',
            pwd: 'senhaforte',
            c_id: 999,
            card: '4111222233334444',
        }),
    });

    assert.equal(res.status, 404);
    assert.equal(res.body, 'Curso não encontrado');
});

test('DELETE /api/users/:id sem token retorna 401', async () => {
    const res = await request('/api/users/1', { method: 'DELETE' });
    assert.equal(res.status, 401);
});

test('DELETE /api/users/:id remove usuário e dependências', async () => {
    const res = await request('/api/users/1', { method: 'DELETE', headers: ADMIN_HEADERS });
    assert.equal(res.status, 200);
    assert.equal(res.body, 'Usuário deletado com sucesso.');

    const report = await request('/api/admin/financial-report', { headers: ADMIN_HEADERS });
    assert.deepEqual(report.body[0], {
        course: 'Clean Architecture',
        revenue: 0,
        students: [],
    });
});

test('DELETE /api/users/:id retorna 404 para usuário inexistente', async () => {
    const res = await request('/api/users/999', { method: 'DELETE', headers: ADMIN_HEADERS });
    assert.equal(res.status, 404);
    assert.equal(res.body, 'Usuário não encontrado');
});

test('DELETE /api/users/:id rejeita id inválido com 400', async () => {
    const res = await request('/api/users/abc', { method: 'DELETE', headers: ADMIN_HEADERS });
    assert.equal(res.status, 400);
    assert.equal(res.body, 'Bad Request');
});

test('POST /api/checkout para usuário existente com pwd correta retorna 200 (SEC-04)', async () => {
    const res = await request('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usr: 'Guilherme',
            eml: 'gui@fullcycle.com.br',
            pwd: 'senhaforte',
            c_id: 1,
            card: '4111222233334444',
        }),
    });

    assert.equal(res.status, 200);
    assert.equal(res.body.msg, 'Sucesso');
    assert.ok(Number.isInteger(res.body.enrollment_id));
});
