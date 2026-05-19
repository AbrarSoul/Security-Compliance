# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> RBAC protected routes >> audit page denied for standard user
- Location: e2e/dashboard.spec.ts:194:7

# Error details

```
Error: browserType.launch: Executable doesn't exist at /var/folders/d5/5xvkptzs6cd9t_077gyhh1400000gr/T/cursor-sandbox-cache/badac33934d48ee0d667559c96a8608d/playwright/chromium_headless_shell-1223/chrome-headless-shell-mac-arm64/chrome-headless-shell
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
```