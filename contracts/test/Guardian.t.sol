// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {DemoVault} from "../src/DemoVault.sol";
import {Guardian} from "../src/Guardian.sol";

contract Actor {
    function pause(Guardian guardian, bytes32 incidentRef, uint8 severity) external {
        guardian.pause(incidentRef, severity);
    }

    function unpause(Guardian guardian, bytes32 reasonHash) external {
        guardian.unpause(reasonHash);
    }

    function unsafeWithdrawFrom(DemoVault vault, address account, uint256 amount) external {
        vault.unsafeWithdrawFrom(account, amount);
    }
}

contract GuardianTest {
    Guardian private guardian;
    DemoVault private vault;
    Actor private keeper;
    Actor private outsider;

    bytes32 private constant INCIDENT = keccak256("incident-v1");
    bytes32 private constant REASON = keccak256("human-reviewed");

    function setUp() public {
        keeper = new Actor();
        outsider = new Actor();
        guardian = new Guardian(address(this), address(keeper));
        vault = new DemoVault(address(guardian));
    }

    function testKeeperCanPauseAndVaultReadsGuardian() public {
        vault.faucetCredit(address(this), 100);
        keeper.pause(guardian, INCIDENT, 3);

        require(guardian.paused(), "guardian must be paused");
        (bool ok,) = address(vault).call(abi.encodeCall(DemoVault.withdraw, (1)));
        require(!ok, "vault withdrawal must be blocked");
        require(vault.demoCredits(address(this)) == 100, "credit must remain unchanged");
    }

    function testKeeperCannotUnpause() public {
        keeper.pause(guardian, INCIDENT, 3);

        (bool ok,) = address(keeper).call(abi.encodeCall(Actor.unpause, (guardian, REASON)));
        require(!ok, "keeper must not unpause");
        require(guardian.paused(), "failed escalation must not change state");
    }

    function testOwnerCanUnpauseWithReason() public {
        keeper.pause(guardian, INCIDENT, 3);
        guardian.unpause(REASON);
        require(!guardian.paused(), "owner must restore availability");
    }

    function testOutsiderCannotPause() public {
        (bool ok,) = address(outsider).call(abi.encodeCall(Actor.pause, (guardian, INCIDENT, 3)));
        require(!ok, "outsider must not pause");
        require(!guardian.paused(), "failed call must not change state");
    }

    function testDuplicateIncidentReferenceCannotBeReused() public {
        keeper.pause(guardian, INCIDENT, 3);
        guardian.unpause(REASON);

        (bool ok,) = address(keeper).call(abi.encodeCall(Actor.pause, (guardian, INCIDENT, 3)));
        require(!ok, "incident reference must be one-use");
        require(!guardian.paused(), "duplicate reference must not change state");
    }

    function testInvalidSeverityCannotPause() public {
        (bool ok,) = address(keeper).call(abi.encodeCall(Actor.pause, (guardian, INCIDENT, 4)));
        require(!ok, "invalid severity must fail");
        require(!guardian.paused(), "invalid severity must not change state");
    }

    function testIntentionalDemoVulnerabilityWorksBeforePause() public {
        vault.faucetCredit(address(this), 100);
        outsider.unsafeWithdrawFrom(vault, address(this), 40);
        require(vault.demoCredits(address(this)) == 60, "unsafe withdrawal must emit signal");
    }

    function testOwnerCanRevokeKeeper() public {
        guardian.setKeeper(address(keeper), false);
        (bool ok,) = address(keeper).call(abi.encodeCall(Actor.pause, (guardian, INCIDENT, 3)));
        require(!ok, "revoked keeper must not pause");
    }

    function testOwnerCannotAlsoBeKeeper() public {
        (bool ok,) = address(guardian).call(abi.encodeCall(Guardian.setKeeper, (address(this), true)));
        require(!ok, "owner and keeper roles must stay separate");
    }
}
