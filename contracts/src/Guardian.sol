// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/// @title NexGuard Sentinel Guardian
/// @notice Demo-only pause authority for Base Sepolia. It never holds funds.
/// @dev Keepers can only reduce availability by pausing. Only the human owner
///      can restore availability, and every transition carries an audit hash.
contract Guardian {
    error AlreadyPaused();
    error DuplicateIncidentReference(bytes32 incidentRef);
    error InvalidAddress();
    error InvalidReference();
    error InvalidSeverity(uint8 severity);
    error NotPaused();
    error UnauthorizedKeeper(address caller);
    error UnauthorizedOwner(address caller);

    event KeeperUpdated(address indexed keeper, bool allowed);
    event Paused(bytes32 indexed incidentRef, uint8 severity, address indexed keeper);
    event Unpaused(bytes32 indexed reasonHash, address indexed owner);

    address public immutable owner;
    bool public paused;

    mapping(address keeper => bool allowed) public keepers;
    mapping(bytes32 incidentRef => bool used) public usedIncidentRefs;

    constructor(address initialOwner) {
        if (initialOwner == address(0)) revert InvalidAddress();
        owner = initialOwner;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert UnauthorizedOwner(msg.sender);
        _;
    }

    modifier onlyKeeper() {
        if (!keepers[msg.sender]) revert UnauthorizedKeeper(msg.sender);
        _;
    }

    function setKeeper(address keeper, bool allowed) external onlyOwner {
        if (keeper == address(0)) revert InvalidAddress();
        keepers[keeper] = allowed;
        emit KeeperUpdated(keeper, allowed);
    }

    function pause(bytes32 incidentRef, uint8 severity) external onlyKeeper {
        if (incidentRef == bytes32(0)) revert InvalidReference();
        if (severity == 0 || severity > 3) revert InvalidSeverity(severity);
        if (usedIncidentRefs[incidentRef]) {
            revert DuplicateIncidentReference(incidentRef);
        }
        if (paused) revert AlreadyPaused();

        usedIncidentRefs[incidentRef] = true;
        paused = true;
        emit Paused(incidentRef, severity, msg.sender);
    }

    function unpause(bytes32 reasonHash) external onlyOwner {
        if (reasonHash == bytes32(0)) revert InvalidReference();
        if (!paused) revert NotPaused();

        paused = false;
        emit Unpaused(reasonHash, msg.sender);
    }
}
