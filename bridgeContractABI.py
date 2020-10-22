ABI = """[
    {
      "constant": true,
      "inputs": [
        {
          "name": "",
          "type": "bytes32"
        }
      ],
      "name": "txidRedeemed",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "view",
      "type": "function",
      "signature": "0x7a1fe3b1"
    },
    {
      "constant": true,
      "inputs": [
        {
          "name": "",
          "type": "bytes32"
        }
      ],
      "name": "allowedToMint",
      "outputs": [
        {
          "name": "",
          "type": "address"
        }
      ],
      "payable": false,
      "stateMutability": "view",
      "type": "function",
      "signature": "0x85011102"
    },
    {
      "constant": true,
      "inputs": [
        {
          "name": "",
          "type": "bytes32"
        }
      ],
      "name": "headers",
      "outputs": [
        {
          "name": "digest",
          "type": "bytes32"
        },
        {
          "name": "version",
          "type": "uint32"
        },
        {
          "name": "prevHash",
          "type": "bytes32"
        },
        {
          "name": "merkleRoot",
          "type": "bytes32"
        },
        {
          "name": "timestamp",
          "type": "uint32"
        },
        {
          "name": "target",
          "type": "uint256"
        },
        {
          "name": "nonce",
          "type": "uint32"
        }
      ],
      "payable": false,
      "stateMutability": "view",
      "type": "function",
      "signature": "0x9e7f2700"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "name": "txid",
          "type": "bytes32"
        },
        {
          "indexed": true,
          "name": "senderEthAddress",
          "type": "address"
        },
        {
          "indexed": false,
          "name": "amountMinted",
          "type": "uint256"
        }
      ],
      "name": "Minted",
      "type": "event",
      "signature": "0x1a49076e0e8c733171c5360d78c9ae8e19fef5a0720b926e72f78b7cc37618cd"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "name": "txid",
          "type": "bytes32"
        },
        {
          "indexed": true,
          "name": "blockHash",
          "type": "bytes32"
        },
        {
          "indexed": true,
          "name": "recipientEthAddress",
          "type": "address"
        },
        {
          "indexed": false,
          "name": "amountRedeemed",
          "type": "uint256"
        }
      ],
      "name": "Redeemed",
      "type": "event",
      "signature": "0x58cf9b93b64457f8d6c726f20c21486907f61e73a340038621b4bc0022631020"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": false,
          "name": "msg",
          "type": "string"
        }
      ],
      "name": "ErrorMessage",
      "type": "event",
      "signature": "0xa183e9a5f6222d4c98fb5b98e0442aaabd70de89b6ec74508bce501a2441f5f9"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "name": "_digest",
          "type": "bytes32"
        }
      ],
      "name": "HeaderStored",
      "type": "event",
      "signature": "0x427e146eb77f78634ac427a2df3843d7b1ac94e69f5012494f981569a1c275c1"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "_tx",
          "type": "bytes"
        },
        {
          "name": "_tokenAddress",
          "type": "address"
        }
      ],
      "name": "checkAndMint",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function",
      "signature": "0xf6761009"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "_blockHash",
          "type": "bytes32"
        },
        {
          "name": "_merkleProof",
          "type": "bytes"
        },
        {
          "name": "_indexOfTxInBlock",
          "type": "uint256"
        },
        {
          "name": "_outputIndexOfBurn",
          "type": "uint8"
        },
        {
          "name": "_tx",
          "type": "bytes"
        }
      ],
      "name": "withdrawTokens",
      "outputs": [
        {
          "name": "",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function",
      "signature": "0xee6c33d3"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "_header",
          "type": "bytes"
        }
      ],
      "name": "parseAndStoreHeader",
      "outputs": [
        {
          "name": "",
          "type": "bytes32"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function",
      "signature": "0xe6a3d4b7"
    },
    {
      "constant": true,
      "inputs": [
        {
          "name": "_val",
          "type": "uint256"
        }
      ],
      "name": "test",
      "outputs": [
        {
          "name": "",
          "type": "uint256"
        }
      ],
      "payable": false,
      "stateMutability": "pure",
      "type": "function",
      "signature": "0x29e99f07"
    }
  ]"""