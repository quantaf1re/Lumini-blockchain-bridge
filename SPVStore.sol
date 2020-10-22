pragma solidity 0.4.25;

/** @title Bridge */
/** @author Quantaf1re, with credit to Summa (https://summa.one) for the SPV validation */

import {ValidateSPV} from "./ValidateSPV.sol";
import {BTCUtils} from "./BTCUtils.sol";
import {BytesLib} from "./BytesLib.sol";
import {SafeMath} from "./SafeMath.sol";


interface IERC20 {
    function totalSupply() external view returns (uint256);

    function balanceOf(address who) external view returns (uint256);

    function allowance(address owner, address spender) external view returns (uint256);

    function transfer(address to, uint256 value) external returns (bool);

    function approve(address spender, uint256 value) external returns (bool);

    function transferFrom(address from, address to, uint256 value) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint256 value);

    event Approval(address indexed owner, address indexed spender, uint256 value);
}


contract Bridge {

    using ValidateSPV for bytes;
    using ValidateSPV for bytes32;
    using BTCUtils for bytes;
    using BytesLib for bytes;
    using SafeMath for uint256;

    // Txid maps to token contract address. A txid with a non-zero value mapped so it indicates that the txid has
    // been marked as allowed to be minted on the btc/MW chain, and the _tokenAddress indicates the asset type.
    // Could be done as an array, but mappings are a bit easier to work with. Every txid is unique, whereas multiple
    // txids can have the same contract. Since Bitcoin only supports one type of asset, we can only use 1 erc20 for
    // testing, but I'm coding this in a way that is generalisable to any erc20 for future use. Only the txid needs
    // to be recorded because when a node receives a btc/mw tx and doesn't find it in its utxo set, it will need to
    // check this allowedToMint to see if the txid is included = the whole tx doesn't need to be stored because the
    // node querying this contract already received the full tx from the mempool and knows the amount in the tx, and
    // the contract knows that the amount in the tx is correct because it verified it with the full tx before adding
    // the txid to allowedToMint
    mapping (bytes32 => address) public allowedToMint;
    // Keep a mapping of txids to know whether coins that were burned have already had the tokens redeemed. This assumes
    // that there is only 1 output per tx that burns coins, which should be the typical case and will be the behaviour
    // of the client software when burning
    mapping (bytes32 => bool) public txidRedeemed;

    event Minted(bytes32 indexed txid, address indexed senderEthAddress, uint256 amountMinted);
    event Redeemed(bytes32 indexed txid, bytes32 indexed blockHash, address indexed recipientEthAddress, uint256 amountRedeemed);

    function checkAndMint(bytes _tx, address _tokenAddress) public returns (bool) {
        // Get the tokenAmount of tokens approved to be spent by this contract
        IERC20 tokenContract = IERC20(_tokenAddress);
        uint256 tokenAmount = tokenContract.allowance(msg.sender, address(this));
        require(tokenAmount > 0, "Don't bloat the chain.");

        // Parse the tx to get the txid
        // parseTransactionReturnTxid can be used here instead with a modification to support nOuts
        bytes memory nIns;
        bytes memory ins;
        bytes memory nOuts;
        bytes memory outs;
        bytes memory locktime;
        bytes32 txid;
        (nIns, ins, nOuts, outs, locktime, txid) = _tx.parseTransaction();

        // There's nothing stopping multiple outputs being specified in the future, just not now for simplicity
        require(keccak256(nOuts) == keccak256(abi.encodePacked(uint8(1))), "Only 1 output allowed for simplicity, splitting can be done on the MW chain.");

        // Need the amount to be minted to match the amount of tokens sent. Because Eth tokens typically have 18 decimal
        // places and Bitcoin has 8, in order to retain 1 token looking like 1 coin, and to avoid having ridiculously
        // large numbers on minted Bitcoin, the tokenAmount is divided to have the same decimal places as Bitcoin
        uint256 outputValue = _tx.extractOutputAtIndex(0).extractValue();
        // Might run into an issue here where the precision loss makes this fail?
        require(outputValue == (tokenAmount/(10**10)), "Supplied tx doesn't have the correct number of coins in its output");

        // Add lines about requiring the rolling value of tokens minted to not be over a certain value to protect against
        // reorgs. Instead of requiring someone to constantly update the prices of all tokens in existence in order to
        // check the $ value of a minting, a user could supply the price of the token themselves (which would be
        // automatically done by the client software), and during some time period, anyone has the opportunity to
        // challenge it during some time period. If the challenger supplies a proof that the price is false, then the
        // minting is reversed and the challenger takes a % of the user's tokens, and the rest of the tokens are sent
        // back to the user. As long as there are atleast a couple of machines online at any one time that are running
        // scripts to check new mints for potential challenges, that should ensure the $ amount of mints doesn't go over

        // Transfer the tokens to this contract. It is done like this so
        // that the contract knows the user who is calling this function is the owner
        // of the funds being sent, so authentication is built in, and so it knows
        // the amount the user sent. Leave until last
        require(tokenContract.transferFrom(msg.sender, address(this), tokenAmount), "Transfer failed");

        // Add the txid to a mapping, once verified, that nodes can easily query
        allowedToMint[txid] = _tokenAddress;
        emit Minted(txid, msg.sender, outputValue);
        return true;
    }


    function withdrawTokens(
        bytes32 _blockHash,
        bytes _merkleProof,
        uint256 _indexOfTxInBlock,
        uint8 _outputIndexOfBurn,
        bytes _tx
    ) public returns (bool) {
        // Parse the supplied tx, make sure it matches the merkleProof and is included in the block
        bytes32 txid = _tx.parseTransactionReturnTxid();
        require(txidRedeemed[txid] == false, "tx already redeemed");
        require(txid.prove(headers[_blockHash].merkleRoot, _merkleProof, _indexOfTxInBlock), "Proof invalid");

        // Parse the specified output
        uint8 outputType;
        TxOut storage output;
        (output.value, outputType, output.payload) = _tx.extractOutputAtIndex(_outputIndexOfBurn).parseOutput();

        // Make sure the output is an OP_RETURN, and the data is consistent with being an Ethereum address
        require(outputType == 3, "Not a OP_RETURN/burn output");
        // First 20 bytes is the token address, next 20 is the recipient's Eth address
        require(output.payload.length == 40, "Data length != 40 bytes");

        // Send the tokens to the recipient. Doing it thi                                                                                                                                           s way means that if user A burns tokens on MW, anyone can call
        // this function to send the tokens to the address that A specified in the burn - there's no reason why anyone
        // would pay gas for transfer someone else's tokens, but it's possible.
        IERC20 tokenContract = IERC20((output.payload.slice(0, 20)).bytesToAddress());
        // address recipient = (output.payload).bytesToAddress();
        // Need to account for the differences in decimals between Eth and Btc. It would be nice to have recipientEthAddress
        // and tokenAmount variables to reduce repeated calculations, but then I get a 'stack too deep' error :|
        require(tokenContract.transfer((output.payload.slice(20, 20)).bytesToAddress(), output.value * 10**10), "Transfer failed");
        // Prevent double-redemptions in the future
        txidRedeemed[txid] = true;
        emit Redeemed(txid, _blockHash, (output.payload.slice(20, 20)).bytesToAddress(), output.value * 10**10);
        return true;
    }




    event HeaderStored(bytes32 indexed _digest);

    enum OutputTypes { NONE, WPKH, WSH, OP_RETURN }

    struct TxOut {
        uint64 value;               // 8 byte value
        OutputTypes outputType;
        bytes payload;              // pubkey hash, script hash, or OP_RETURN data
    }

    struct Header {
        bytes32 digest;             // 32 byte little endian digest
        uint32 version;             // 4 byte version
        bytes32 prevHash;           // 32 byte previous block hash
        bytes32 merkleRoot;         // 32 byte tx root
        uint32 timestamp;           // 4 byte timestamp
        uint256 target;             // 4 byte nBits == 32 byte integer
        uint32 nonce;               // 4 byte nonce
    }

    mapping(bytes32 => Header) public headers;              // Parsed headers

    /// @notice             Parses a header and stores to the mapping
    /// @param _header      The raw byte header
    /// @return             true if valid format, false otherwise
    function parseAndStoreHeader(bytes _header) public returns (bytes32) {

        bytes32 _digest;
        uint32 _version;
        bytes32 _prevHash;
        bytes32 _merkleRoot;
        uint32 _timestamp;
        uint256 _target;
        uint32 _nonce;

        (_digest, _version, _prevHash, _merkleRoot, _timestamp, _target, _nonce) = _header.parseHeader();

        headers[_digest].digest = _digest;
        headers[_digest].version = _version;
        headers[_digest].prevHash = _prevHash;
        headers[_digest].merkleRoot = _merkleRoot;
        headers[_digest].timestamp = _timestamp;
        headers[_digest].target = _target;
        headers[_digest].nonce = _nonce;

        // Emit HeaderStored event
        emit HeaderStored(_digest);

        // Return header digest
        return _digest;
    }

    function test(uint256 _val) public pure returns (uint256) {
        return _val;
    }

// Made these functions because withdrawTokens was giving a 'stack too deep' error - the intention was from:
    // Split this function into : 1) verifying the tx for a given block and adding the txid to a mapping of
    // txid => (bool) where the bool indicates whether the tokens were redeemed or not (the existence of a
    // non-zero value mapped from the txid key indicates successful validation), and 2) checking the output
    // type and sending the tokens
    //
    // function checkTxInBlock(
    //     bytes _tx,
    //     bytes32 _blockHash,
    //     bytes _merkleProof,
    //     uint256 _indexOfTxInBlock
    // ) public returns (bool) {
    //     require(txRedemptionLevel[txid] == 0, "tx already atleast partially redeemed");
    //     // Parse the supplied tx, make sure it matches the merkleProof and is included in the block
    //     bytes32 txid = _tx.parseTransactionReturnTxid();
    //     require(txid.prove(headers[_blockHash].merkleRoot, _merkleProof, _indexOfTxInBlock), "Proof invalid");
    //     txRedemptionLevel[txid] = 1;
    //     return true;
    // }

    // function checkOutputAndWithdraw(
    //     bytes _tx,
    //     uint8 _outputIndexOfBurn
    // ) public returns (bool) {

    //     bytes32 txid = _tx.parseTransactionReturnTxid();
    //     require(txRedemptionLevel[txid] == 1, "Existence in block not confirmed or token withdrawal has already happened");

    //     // Parse the specified output
    //     // Might be able to change to a different variable type for outputType so that memory can be used
    //     uint8 outputType;
    //     // Could similarly just use memory vaiables here
    //     TxOut storage output;
    //     (output.value, outputType, output.payload) = _tx.extractOutputAtIndex(_outputIndexOfBurn).parseOutput();

    //     // Make sure the output is an OP_RETURN, and the data is consistent with being an Ethereum address
    //     require(outputType == 3, "Not a OP_RETURN/burn output");
    //     require(output.payload.length == 40, "Data length != 40 bytes");

    //     // Send the tokens to the recipient. Doing it this way means that if user A burns tokens on MW, anyone can call
    //     // this function to send the tokens to the address that A specified in the burn - there's no reason why anyone
    //     // would pay gas for transfer someone else's tokens, but it's possible.
    //     IERC20 tokenContract = IERC20(bytesToAddress(output.payload.slice(0, 20)));
    //     // Need to account for the differences in decimals between Eth and Btc. Should look into how much precision is
    //     // lost here and if it makes some Wei of tokens unwithdrawable
    //     require(tokenContract.transfer(bytesToAddress(output.payload.slice(20, 20)), output.value * 10**10), "Transfer failed");
    //     // Prevent double-redemptions in the future
    //     txRedemptionLevel[txid] = 2;
    //     return true;
    // }
}
