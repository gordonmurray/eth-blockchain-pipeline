// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PurchaseStore
 * @dev A simple smart contract that emits purchase events for learning purposes.
 * This simulates a store where buyers can make purchases of products.
 */
contract PurchaseStore {
    // Event emitted when a purchase is made
    event PurchaseMade(
        address indexed buyer,
        uint256 indexed productId,
        uint256 price,
        uint256 quantity,
        uint256 timestamp
    );

    // Store owner
    address public owner;

    // Product catalog (productId => price in wei)
    mapping(uint256 => uint256) public productPrices;

    // Track total purchases
    uint256 public totalPurchases;

    // Track total revenue
    uint256 public totalRevenue;

    constructor() {
        owner = msg.sender;

        // Initialize some default products (prices in wei)
        // Product 1: Coffee - 0.001 ETH
        productPrices[1] = 1000000000000000;
        // Product 2: Sandwich - 0.005 ETH
        productPrices[2] = 5000000000000000;
        // Product 3: Pizza - 0.01 ETH
        productPrices[3] = 10000000000000000;
        // Product 4: Burger - 0.008 ETH
        productPrices[4] = 8000000000000000;
        // Product 5: Salad - 0.006 ETH
        productPrices[5] = 6000000000000000;
    }

    /**
     * @dev Make a purchase
     * @param productId The ID of the product to purchase
     * @param quantity The quantity to purchase
     */
    function purchase(uint256 productId, uint256 quantity) external payable {
        require(productId >= 1 && productId <= 5, "Invalid product ID");
        require(quantity > 0, "Quantity must be greater than 0");

        uint256 expectedPrice = productPrices[productId] * quantity;
        require(msg.value >= expectedPrice, "Insufficient payment");

        totalPurchases++;
        totalRevenue += msg.value;

        emit PurchaseMade(
            msg.sender,
            productId,
            msg.value,
            quantity,
            block.timestamp
        );

        // Refund excess payment
        if (msg.value > expectedPrice) {
            payable(msg.sender).transfer(msg.value - expectedPrice);
        }
    }

    /**
     * @dev Get product price
     * @param productId The ID of the product
     * @return The price in wei
     */
    function getProductPrice(uint256 productId) external view returns (uint256) {
        require(productId >= 1 && productId <= 5, "Invalid product ID");
        return productPrices[productId];
    }

    /**
     * @dev Withdraw collected funds (owner only)
     */
    function withdraw() external {
        require(msg.sender == owner, "Only owner can withdraw");
        payable(owner).transfer(address(this).balance);
    }

    /**
     * @dev Get contract balance
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
