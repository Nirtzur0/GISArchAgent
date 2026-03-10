import { defineConfig } from "@playwright/test";
export default defineConfig({
    testDir: "./tests",
    timeout: 60000,
    use: {
        baseURL: "http://127.0.0.1:8001",
        headless: true
    },
    webServer: {
        command: "npm run build && ../scripts/run_test_stack.sh",
        url: "http://127.0.0.1:8001",
        reuseExistingServer: true,
        timeout: 180000
    }
});
