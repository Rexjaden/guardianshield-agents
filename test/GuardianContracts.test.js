const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("GuardianShield Contracts", function () {
  let deployer, user1, user2;
  let guardianToken, guardianShieldToken, guardianStaking;

  beforeEach(async function () {
    [deployer, user1, user2] = await ethers.getSigners();

    // Deploy GuardianToken
    const GuardianToken = await ethers.getContractFactory("GuardianToken");
    guardianToken = await GuardianToken.deploy(deployer.address);

    // Deploy GuardianShieldToken
    const GuardianShieldToken = await ethers.getContractFactory("GuardianShieldToken");
    guardianShieldToken = await GuardianShieldToken.deploy();

    // Deploy GuardianStaking
    const GuardianStaking = await ethers.getContractFactory("GuardianStaking");
    guardianStaking = await GuardianStaking.deploy(
      await guardianToken.getAddress(),
      ethers.parseEther("1") // 1 token per second reward
    );
  });

  describe("GuardianToken", function () {
    it("Should have correct initial supply", async function () {
      const expectedSupply = ethers.parseEther("300000000"); // 300M tokens
      expect(await guardianToken.totalSupply()).to.equal(expectedSupply);
    });

    it("Should have correct name and symbol", async function () {
      expect(await guardianToken.name()).to.equal("Guardian Token");
      expect(await guardianToken.symbol()).to.equal("GUARD");
    });

    it("Should allow owner to mint additional stages", async function () {
      const mintAmount = ethers.parseEther("100000000"); // 100M tokens
      await guardianToken.mintStage(user1.address, mintAmount);
      
      expect(await guardianToken.balanceOf(user1.address)).to.equal(mintAmount);
    });
  });

  describe("GuardianShieldToken", function () {
    it("Should have correct name and symbol", async function () {
      expect(await guardianShieldToken.name()).to.equal("GuardianShieldToken");
      expect(await guardianShieldToken.symbol()).to.equal("GST");
    });

    it("Should allow owner to mint NFTs with serial numbers", async function () {
      const serial = 12345;
      const tokenURI = "https://guardian-shield.io/nft/12345";
      
      await guardianShieldToken.mintWithSerial(user1.address, serial, tokenURI);
      
      const tokenId = await guardianShieldToken.serialToTokenId(serial);
      expect(await guardianShieldToken.ownerOf(tokenId)).to.equal(user1.address);
      expect(await guardianShieldToken.tokenIdToSerial(tokenId)).to.equal(serial);
    });
  });

  describe("GuardianStaking", function () {
    beforeEach(async function () {
      // Transfer some tokens to users for testing
      await guardianToken.transfer(user1.address, ethers.parseEther("1000"));
      await guardianToken.transfer(user2.address, ethers.parseEther("1000"));
    });

    it("Should allow users to stake tokens", async function () {
      const stakeAmount = ethers.parseEther("100");
      
      // Approve staking contract
      await guardianToken.connect(user1).approve(await guardianStaking.getAddress(), stakeAmount);
      
      // Stake tokens
      await guardianStaking.connect(user1).stake(stakeAmount);
      
      const stakeInfo = await guardianStaking.stakes(user1.address);
      expect(stakeInfo.amount).to.equal(stakeAmount);
    });

    it("Should have correct staking token address", async function () {
      expect(await guardianStaking.guardToken()).to.equal(await guardianToken.getAddress());
    });
  });
});