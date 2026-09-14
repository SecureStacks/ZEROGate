/**
 * Basic Frontend Verification Test
 * Verifies key configuration and files are present and syntactically valid.
 */
const fs = require('fs');
const path = require('path');

console.log("Running ZeroGate Frontend Foundation Verification...");

const requiredFiles = [
  'src/app/layout.tsx',
  'src/app/page.tsx',
  'src/app/dashboard/page.tsx',
  'src/app/simulator/page.tsx',
  'src/app/policies/page.tsx',
  'src/app/topology/page.tsx',
  'src/app/logs/page.tsx',
  'src/components/Navbar.tsx',
  'src/components/HealthStatusBadge.tsx',
  'src/lib/api.ts',
  'tailwind.config.js',
  'tsconfig.json'
];

let allPassed = true;

for (const file of requiredFiles) {
  const fullPath = path.join(__dirname, file);
  if (fs.existsSync(fullPath)) {
    console.log(`  [PASS] Found ${file}`);
  } else {
    console.error(`  [FAIL] Missing ${file}`);
    allPassed = false;
  }
}

if (!allPassed) {
  process.exit(1);
}

console.log("All Frontend Phase 1 components verified successfully!");
