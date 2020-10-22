pragma solidity = 0.5.2;

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

// Need to add SafeMath and asset type to struct
contract Bridge {
    
    
    struct Output {
        string output;
        uint256 amount;
        uint256 nonce;
        address assetType;
    }
    
    struct MWTransaction {
        string commitment;
        uint256 amount;
        address assetType;
    }
    
    struct MWBlockHeader {
        bytes32 previousHash;
        bytes32 hash;
        uint256 height;
        bytes32 merkleroot;
        uint256 difficulty;
    }
    
    // Could be done as an array, but mappings are a bit easier to work with
    mapping (uint256 => Output) allowedToMint;
    // Used to differentiate between duplicate Outputs
    uint256 outputGenNonce = 0;
    address allowedToUpdatePrices;
    address commissionReceiver;
    // Saves the Eth prices of tokens by contract for charging a commission. If a
    // token doesn't have its price included, then the price is 0 and therefore no
    // commission is charged. 8 decimal places
    mapping (address => uint256) tokenPricesInEth;
    mapping (uint256 => MWBlockHeader) blockHeaders;
    
    
    constructor(address _commissionReceiver) public {
        allowedToUpdatePrices = msg.sender;
        commissionReceiver = _commissionReceiver;
    }
    
    function checkAndMint(address _tokenAddress, string memory _hexOutput) public returns (bool) {
        // Get the tokenAmount of tokens approved to be spent by this contract
        IERC20 tokenContract  = IERC20(_tokenAddress);
        uint256 tokentokenAmount = tokenContract.allowance(msg.sender, address(this));
        require(tokenAmount > 0, "Don't bloat the chain.");
        
        // Actually transfer the tokens to this contract. It is done like this so
        // that the contract knows the user who is calling this function is the owner
        // of the funds being sent, so authentication is built in
        require(tokenContract.transferFrom(msg.sender, address(this), tokenAmount));
        
        // Add an Output with the MW hex output that can only be spent by the user specified in it
        allowedToMint[outputGenNonce] = Output(_hexOutput, tokenAmount, outputGenNonce, _tokenAddress);
        
        outputGenNonce += 1;
        return true;
    }
    
    function checkTransactionExistence(uint256 _MWHeight, string memory _MWTx, string memory _MWMerkleproof) public returns (bool) {
        // Check existence
        return true;
    }
    
    function decodeMWTx(string memory _MWTx) public returns (MWTransaction) {
        
    }
    
    function withdrawTokens(uint256 _MWHeight, string memory _MWTx, string memory _MWMerkleproof) public returns (bool) {
        require(checkTransactionExistence(_MWHeight, _MWTx, _MWMerkleproof));
        decodedMWTx = decodeMWTx(_MWTx);
        tokenAmount = decodedMWTx.amount;
        
        require(msg.value >= (tokenAmount * tokenPricesInEth[_tokenAddress] / (500 * 10**8)));
        IERC20 tokenContract  = IERC20(_tokenAddress);
        tokenContract.transfer(msg.sender, tokenAmount);
        return true;
    }
    
    function withdrawEth() public {
        require(msg.sender == commissionReceiver);
        commissionReceiver.transfer(this.balance);
    }
}
