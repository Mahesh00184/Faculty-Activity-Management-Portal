const fs = require('fs');
const path = require('path');

const directoryPath = path.join(__dirname, 'frontend/src');

function walkDir(dir) {
    fs.readdirSync(dir).forEach(file => {
        let fullPath = path.join(dir, file);
        if (fs.lstatSync(fullPath).isDirectory()) {
            walkDir(fullPath);
        } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
            if (fullPath.includes('api.ts')) return; // handled separately
            
            let content = fs.readFileSync(fullPath, 'utf8');
            let modified = false;

            if (content.includes('http://localhost:8000/api')) {
                content = content.replace(/http:\/\/localhost:8000\/api/g, '${API_BASE_URL}');
                modified = true;
            }
            if (content.includes('http://localhost:8000/')) {
                // For certificate uploads/views which used `http://localhost:8000/` without api
                content = content.replace(/http:\/\/localhost:8000\//g, '${API_BASE_URL.replace("/api", "")}/');
                modified = true;
            }

            if (modified) {
                // Ensure import of API_BASE_URL
                if (!content.includes('API_BASE_URL')) {
                    if (content.includes("import { api } from '../services/api';")) {
                        content = content.replace("import { api } from '../services/api';", "import { api, API_BASE_URL } from '../services/api';");
                    }
                }
                fs.writeFileSync(fullPath, content);
            }
        }
    });
}

walkDir(directoryPath);
console.log('Completed replacement');
