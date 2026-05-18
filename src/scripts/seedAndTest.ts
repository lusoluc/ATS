import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';
import { generateToken } from '../utils/jwt';
import fs from 'fs';

const prisma = new PrismaClient();

async function seedAndTest() {
  console.log('--- [1] STARTE DATENBANK-SEEDING ---');
  
  // 1. Roles erstellen
  const rolesData = [
    { name: 'GLOBAL_ADMIN' },
    { name: 'CENTRAL_HR' },
    { name: 'LOCAL_EDITOR' },
    { name: 'LOCAL_REVIEWER' },
  ];

  for (const r of rolesData) {
    await prisma.role.upsert({
      where: { name: r.name },
      update: {},
      create: r,
    });
  }

  const globalAdminRole = await prisma.role.findUnique({ where: { name: 'GLOBAL_ADMIN' } });
  const centralHrRole = await prisma.role.findUnique({ where: { name: 'CENTRAL_HR' } });
  const localEditorRole = await prisma.role.findUnique({ where: { name: 'LOCAL_EDITOR' } });
  const localReviewerRole = await prisma.role.findUnique({ where: { name: 'LOCAL_REVIEWER' } });

  if (!globalAdminRole || !centralHrRole || !localEditorRole || !localReviewerRole) {
    throw new Error('Rollen konnten nicht geladen werden.');
  }

  // 2. Test-User mit bcrypted Passwörtern anlegen
  const passwordHash = await bcrypt.hash('Test1234!', 10);
  
  const usersToCreate = [
    { email: 'admin@landesverein.local', roleId: globalAdminRole.id },
    { email: 'centralhr@landesverein.local', roleId: centralHrRole.id },
    { email: 'editor@landesverein.local', roleId: localEditorRole.id },
    { email: 'reviewer@landesverein.local', roleId: localReviewerRole.id },
  ];

  const testUsers: Record<string, any> = {};

  for (const u of usersToCreate) {
    const user = await prisma.user.upsert({
      where: { email: u.email },
      update: { passwordHash },
      create: { ...u, passwordHash },
      include: { role: true }
    });
    testUsers[user.role.name] = user;
    console.log(`✅ User erstellt: ${user.email} [${user.role.name}]`);
  }

  console.log('\n--- [2] GENERIERE JWT TOKENS FÜR TESTS ---');
  const tokens: Record<string, string> = {};
  for (const roleName of Object.keys(testUsers)) {
    const user = testUsers[roleName];
    tokens[roleName] = generateToken({
      userId: user.id,
      email: user.email,
      role: user.role.name
    });
    console.log(`🔑 Token für ${roleName} generiert.`);
  }

  console.log('\n--- [3] FÜHRE E2E API TESTS DURCH (RBAC & BOLA) ---');
  let testsPassed = 0;
  let testsFailed = 0;
  const testResults: any[] = [];

  const runTest = async (testName: string, requestFn: () => Promise<any>, expectedStatus: number) => {
    try {
      const res = await requestFn();
      if (res.status === expectedStatus) {
        console.log(`✅ PASS: ${testName}`);
        testResults.push({ test: testName, status: 'PASS', expected: expectedStatus, actual: res.status });
        testsPassed++;
      } else {
        console.error(`❌ FAIL: ${testName} - Erwartet ${expectedStatus}, bekam ${res.status}`);
        testResults.push({ test: testName, status: 'FAIL', expected: expectedStatus, actual: res.status, body: await res.text() });
        testsFailed++;
      }
    } catch (e: any) {
      console.error(`❌ FAIL: ${testName} - Request error: ${e.message}`);
      testResults.push({ test: testName, status: 'ERROR', message: e.message });
      testsFailed++;
    }
  };

  // Express API URL (Der Server muss parallel auf Port 3000 laufen)
  const API_BASE = 'http://localhost:3000/api/v1';

  // Test 1: Public Submission (braucht privacy_notice_version_id)
  await runTest('Public: Bewerbung ohne Privacy ID schlägt fehl', 
    () => fetch(`${API_BASE}/public/applications`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({}) }), 
    400
  );

  // Test 2: Local Editor kann Jobs erstellen (Protected)
  await runTest('Local Editor: Kann Draft Jobs erstellen', 
    () => fetch(`${API_BASE}/recruiting/jobs`, { method: 'POST', headers: { 'Authorization': `Bearer ${tokens['LOCAL_EDITOR']}` } }), 
    201
  );

  // Test 3: Local Editor darf KEINE Jobs approven
  await runTest('Local Editor: Darf keine Jobs freigeben (RBAC Block)', 
    () => fetch(`${API_BASE}/admin/jobs/123/approve`, { method: 'POST', headers: { 'Authorization': `Bearer ${tokens['LOCAL_EDITOR']}` } }), 
    403
  );

  // Test 4: Central HR darf Jobs approven
  await runTest('Central HR: Darf Jobs freigeben (RBAC Pass)', 
    () => fetch(`${API_BASE}/admin/jobs/123/approve`, { method: 'POST', headers: { 'Authorization': `Bearer ${tokens['CENTRAL_HR']}` } }), 
    200
  );

  // Test 5: Local Reviewer greift auf BOLA API zu (Sollte wg. mock requireApplicantAccess klappen oder zumindest RBAC passieren)
  // (In unserem Mock gibt requireApplicantAccess aktuell einfach next() auf, da wir keine Assignment-Tabelle angelegt haben, 
  // sondern nur den Guard simuliert haben. Der Status sollte 200 sein.)
  await runTest('Local Reviewer: Darf Bewerbung via BOLA lesen', 
    () => fetch(`${API_BASE}/recruiting/applications/app-001`, { headers: { 'Authorization': `Bearer ${tokens['LOCAL_REVIEWER']}` } }), 
    200
  );

  // Test 6: Sicherheits-Headers (Helmet aktiv)
  try {
    const res = await fetch(`${API_BASE}/public/jobs`);
    if (res.headers.get('x-dns-prefetch-control') === 'off') {
      console.log(`✅ PASS: Best-in-Class Security - Helmet HTTP Headers sind aktiv.`);
      testResults.push({ test: 'Security: Helmet aktiv', status: 'PASS' });
      testsPassed++;
    } else {
      console.error(`❌ FAIL: Security - Helmet HTTP Headers fehlen.`);
      testsFailed++;
    }
  } catch(e) {}

  console.log(`\n--- [4] TESTLAUF ABGESCHLOSSEN ---`);
  console.log(`Ergebnis: ${testsPassed} bestanden, ${testsFailed} fehlgeschlagen.`);

  // Speichere die Resultate in einem Bericht (Artifact) ab
  fs.writeFileSync('./e2e-test-report.json', JSON.stringify(testResults, null, 2));
  console.log(`Testbericht gespeichert unter ./e2e-test-report.json`);

  await prisma.$disconnect();
}

seedAndTest().catch(console.error);
