// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title Decentralized Malicious Entity Registry (DMER)
 * @dev Registry for tracking malicious entities (addresses, contracts, domains, etc.) on-chain.
 */
contract DMER is Ownable {
    struct Entity {
        string entityType; // e.g., "address", "contract", "domain", "ip"
        string identifier; // e.g., address, contract address, domain name, IP
        string reason;     // Reason for flagging
        uint256 timestamp; // When entity was added
        address reporter;  // Who reported
        bool active;       // Is entity currently flagged
    }

    Entity[] public entities;
    mapping(string => uint256[]) public entityIndex; // identifier => entity indices

    event EntityFlagged(uint256 indexed entityId, string identifier, string entityType, string reason, address reporter);
    event EntityUnflagged(uint256 indexed entityId, string identifier, address reporter);

    function flagEntity(string memory entityType, string memory identifier, string memory reason) public {
        Entity memory newEntity = Entity({
            entityType: entityType,
            identifier: identifier,
            reason: reason,
            timestamp: block.timestamp,
            reporter: msg.sender,
            active: true
        });
        entities.push(newEntity);
        uint256 entityId = entities.length - 1;
        entityIndex[identifier].push(entityId);
        emit EntityFlagged(entityId, identifier, entityType, reason, msg.sender);
    }

    function unflagEntity(uint256 entityId) public onlyOwner {
        require(entityId < entities.length, "Invalid entityId");
        entities[entityId].active = false;
        emit EntityUnflagged(entityId, entities[entityId].identifier, msg.sender);
    }

    function getEntity(uint256 entityId) public view returns (Entity memory) {
        require(entityId < entities.length, "Invalid entityId");
        return entities[entityId];
    }

    function getEntitiesByIdentifier(string memory identifier) public view returns (Entity[] memory) {
        uint256[] memory indices = entityIndex[identifier];
        Entity[] memory result = new Entity[](indices.length);
        for (uint256 i = 0; i < indices.length; i++) {
            result[i] = entities[indices[i]];
        }
        return result;
    }

    function getActiveEntities() public view returns (Entity[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < entities.length; i++) {
            if (entities[i].active) count++;
        }
        Entity[] memory result = new Entity[](count);
        uint256 idx = 0;
        for (uint256 i = 0; i < entities.length; i++) {
            if (entities[i].active) {
                result[idx] = entities[i];
                idx++;
            }
        }
        return result;
    }
}
