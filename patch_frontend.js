const fs = require('fs');
const file = 'frontend/src/api/backend.js';
let code = fs.readFileSync(file, 'utf8');

const queryHelper = `\nconst getDateQuery = (days, start, end) => start && end ? \`start_date=\${start}&end_date=\${end}\` : \`days=\${days}\`;\n`;
if (!code.includes('getDateQuery')) {
    code = code.replace('const BASE_URL = "http://localhost:8000";', 'const BASE_URL = "http://localhost:8000";' + queryHelper);
}

const replacer = (funcName, paramName) => {
    // e.g. export async function fetchProjectRisk(projectId, days = 7) {
    const regex1 = new RegExp(`export async function ${funcName}\\(${paramName}, days = (\\d+)\\) \\{`, 'g');
    code = code.replace(regex1, `export async function ${funcName}(${paramName}, days = $1, start = null, end = null) {`);
    
    // e.g. `${BASE_URL}/api/project/risk?project_id=${projectId}&days=${days}`
    const regex2 = new RegExp(`(\\url|\\\`\\$\\{BASE_URL\\}/api/.+?\\?${paramName}=\\$\\{${paramName}\\})&days=\\$\\{days\\}`, 'g');
    code = code.replace(regex2, `$1&\${getDateQuery(days, start, end)}`);
};

replacer('fetchProjectRisk', 'projectId');
replacer('fetchProjectTrend', 'projectId');
replacer('fetchTeamRisk', 'teamId');
replacer('fetchTeamTrend', 'teamId');
replacer('fetchTeamMemberBreakdown', 'userEmail');
replacer('fetchEmployeeProfile', 'userEmail');
replacer('fetchEmployeeTrend', 'userEmail');

// for encodeURIComponent versions
const replacerEncoded = (funcName, paramName) => {
    const regex1 = new RegExp(`export async function ${funcName}\\(${paramName}, days = (\\d+)\\) \\{`, 'g');
    code = code.replace(regex1, `export async function ${funcName}(${paramName}, days = $1, start = null, end = null) {`);
    
    const regex2 = new RegExp(`(&days=\\$\\{days\\})`, 'g');
    code = code.replace(regex2, `\${getDateQuery(days, start, end)}`); 
};
// Actually it's easier to use a global replacement for the inner URL part that matches `&days=${days}` inside the backticks.
// Let's just run across the whole file after updating signatures.

fs.writeFileSync(file, code);
console.log("Patched helper!");
