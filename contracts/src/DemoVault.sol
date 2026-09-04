// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IGuardian {
    function paused() external view returns (bool);
}

/// @title NexGuard Sentinel Demo Vault
/// @notice Deliberately vulnerable, valueless testnet fixture. Never use it for
///         real assets or production deployments.
contract DemoVault {
    error GuardianPaused();
    error InsufficientDemoCredit(uint256 available, uint256 requested);
    error InvalidAddress();
    error InvalidAmount();

    event DemoCreditIssued(address indexed account, uint256 amount);
    event Withdrawal(
        address indexed account,
        address indexed recipient,
        address indexed triggeredBy,
        uint256 amount,
        uint256 remainingCredit
    );

    IGuardian public immutable guardian;
    mapping(address account => uint256 amount) public demoCredits;

    constructor(address guardianAddress) {
        if (guardianAddress == address(0)) revert InvalidAddress();
        guardian = IGuardian(guardianAddress);
    }

    modifier whenNotPaused() {
        if (guardian.paused()) revert GuardianPaused();
        _;
    }

    /// @notice Issues valueless accounting units so the demo never needs funds.
    function faucetCredit(address account, uint256 amount) external {
        if (account == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        demoCredits[account] += amount;
        emit DemoCreditIssued(account, amount);
    }

    function withdraw(uint256 amount) external whenNotPaused {
        _withdrawFrom(msg.sender, msg.sender, amount);
    }

    /// @notice Intentional vulnerability: anyone can consume another account's
    ///         demo credit. It exists only to generate an incident signal.
    function unsafeWithdrawFrom(address account, uint256 amount) external whenNotPaused {
        _withdrawFrom(account, msg.sender, amount);
    }

    function _withdrawFrom(address account, address recipient, uint256 amount) private {
        if (amount == 0) revert InvalidAmount();
        uint256 available = demoCredits[account];
        if (amount > available) revert InsufficientDemoCredit(available, amount);

        uint256 remaining = available - amount;
        demoCredits[account] = remaining;
        emit Withdrawal(account, recipient, msg.sender, amount, remaining);
    }
}
