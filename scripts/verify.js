const { run } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🔍 Starting contract verification...");
  
  const network = await ethers.provider.getNetwork();
  const deploymentFile = path.join(__dirname, "..", "deployments", `${network.name}-latest.json`);
  
  if (!fs.existsSync(deploymentFile)) {
    console.error("❌ No deployment file found. Run deployment first.");
    process.exit(1);
  }
  
  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  
  console.log(`Verifying contracts on ${network.name}...`);
  console.log();

  for (const [contractName, contractInfo] of Object.entries(deployment.contracts)) {
    try {
      console.log(`🔍 Verifying ${contractName} at ${contractInfo.address}...`);
      
      await run("verify:verify", {
        address: contractInfo.address,
        constructorArguments: contractInfo.constructorArgs,
      });
      
      console.log(`✅ ${contractName} verified successfully!`);
    } catch (error) {
      if (error.message.toLowerCase().includes("already verified")) {
        console.log(`✅ ${contractName} already verified`);
      } else {
        console.error(`❌ Failed to verify ${contractName}:`, error.message);
      }
    }
    console.log();
  }

  console.log("🎉 Verification process completed!");
}

if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { main };