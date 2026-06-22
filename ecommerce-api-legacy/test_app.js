// Testes de validação — ecommerce-api-legacy (Node.js/Express LMS)
const http = require('http')

const { createApp } = require('./src/app')

const app = createApp()
let passed = 0
let failed = 0
let server

function request(method, path, body, headers = {}) {
  return new Promise((resolve) => {
    const payload = body ? JSON.stringify(body) : null
    const opts = {
      hostname: 'localhost',
      port: server.address().port,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
        ...headers,
      },
    }
    const req = http.request(opts, (res) => {
      let data = ''
      res.on('data', (chunk) => (data += chunk))
      res.on('end', () => {
        let json = null
        try { json = JSON.parse(data) } catch {}
        resolve({ status: res.statusCode, body: json, raw: data })
      })
    })
    req.on('error', (e) => resolve({ status: 0, body: null, error: e.message }))
    if (payload) req.write(payload)
    req.end()
  })
}

function check(label, res, expectedStatus, assertion) {
  const statusOk = res.status === expectedStatus
  const assertOk = assertion ? assertion(res.body) : true
  const ok = statusOk && assertOk
  if (ok) {
    passed++
    console.log(`  [PASS] ${label}`)
  } else {
    failed++
    console.log(`  [FAIL] ${label}  (got ${res.status}, body=${JSON.stringify(res.body)})`)
  }
}

async function runTests() {
  console.log('\n=== Projeto 2 — ecommerce-api-legacy ===\n')

  console.log('--- Raiz ---')
  const root = await request('GET', '/')
  check('GET /', root, 200, (b) => b && b.msg)

  console.log('\n--- Checkout ---')
  const approved = await request('POST', '/api/checkout', {
    username: 'Test User', email: 'test@test.com', password: '123',
    course_id: 1, card_number: '4111222233334444',
  })
  check('POST /api/checkout — cartão Visa → 200', approved, 200, (b) => b && b.msg === 'Sucesso')

  const denied = await request('POST', '/api/checkout', {
    username: 'Test2', email: 'test2@test.com', password: '123',
    course_id: 2, card_number: '5111222233334444',
  })
  check('POST /api/checkout — cartão Master → 400 (recusado)', denied, 400, (b) => b && b.error)

  const missingFields = await request('POST', '/api/checkout', { email: 'x@x.com' })
  check('POST /api/checkout — campos ausentes → 400', missingFields, 400)

  const invalidCourse = await request('POST', '/api/checkout', {
    username: 'Test3', email: 'test3@test.com', password: '123',
    course_id: 9999, card_number: '4111222233334444',
  })
  check('POST /api/checkout — curso inexistente → 404', invalidCourse, 404)

  console.log('\n--- Admin (autenticação) ---')
  const reportNoAuth = await request('GET', '/api/admin/financial-report')
  check('GET /api/admin/financial-report — sem token → 401', reportNoAuth, 401)

  const reportBadToken = await request('GET', '/api/admin/financial-report', null, {
    Authorization: 'Bearer token-invalido',
  })
  check('GET /api/admin/financial-report — token inválido → 401', reportBadToken, 401)

  console.log('\n--- Login ---')
  const loginOk = await request('POST', '/api/users/login', {
    email: 'leonan@fullcycle.com.br', password: '123',
  })
  check('POST /api/users/login — credenciais corretas → 200', loginOk, 200, (b) => b && b.token)

  const loginFail = await request('POST', '/api/users/login', {
    email: 'leonan@fullcycle.com.br', password: 'errada',
  })
  check('POST /api/users/login — senha errada → 401', loginFail, 401)

  console.log('\n--- Delete de usuário (protegido) ---')
  const deleteNoAuth = await request('DELETE', '/api/users/1')
  check('DELETE /api/users/1 — sem token → 401', deleteNoAuth, 401)

  console.log(`\n${'='.repeat(40)}`)
  console.log(`Resultado: ${passed} PASS / ${failed} FAIL`)
  console.log(`${'='.repeat(40)}\n`)

  server.close()
  process.exit(failed === 0 ? 0 : 1)
}

server = http.createServer(app)
server.listen(0, () => runTests())
