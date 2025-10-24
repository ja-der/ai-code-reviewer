const fs = require("fs");
const path = require("path");

const FIXED_PROMPT =
  "You're an expert in interpreting code, espcially code changes made between two commits. You will be given the raw git diff to work with. Your purpose is to review the code changes and suggest improvements only if there is scope. Always begin your answer with a code quality rating and a status denoting if improvements are required. Then follow with a very short brief of the changes. Talk about what's good in the code. And end with suggested improvements. You cannot be general and must be specific to the changed code, and do not focus on linting but rather scan for security vulnerabilities and architectural changes. Here is the diff:\n ```";

async function main() {
  try {
    const gitDiffOutput = await executeGitDiffCommand();
    const body = {
      model: "deepseek-r1:1.5b",
      prompt: `${FIXED_PROMPT} ${gitDiffOutput}\`\`\``,
      stream: false,
    };
    const response = await fetch("http://localhost:11434/api/generate?", {
      method: "POST",
      body: JSON.stringify(body),
    });
    const data = await response.json();

    // Get the timestamped filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = path.join("code_review", `response-${timestamp}.md`);

    // Create the directory if it doesn't exist
    fs.mkdirSync(path.dirname(filename), { recursive: true });

    // Write the response to a file with a timestamped name
    fs.writeFileSync(filename, data.response);

    console.log(`Response written to ${filename}`);
  } catch (error) {
    console.error("Error:", error);
    console.log(error.toString());
  }
}

async function executeGitDiffCommand() {
  return new Promise((resolve, reject) => {
    const { exec } = require("child_process");
    exec("git diff HEAD", (error, stdout, stderr) => {
      if (error) {
        reject(stderr);
      } else {
        resolve(stdout);
      }
    });
  });
}

main();
