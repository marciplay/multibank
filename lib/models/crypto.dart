class CryptoAccount {
  final String userId;
  final double fiatBalance;
  final double totalCryptoValue;
  final Map<String, CryptoBalance> cryptoBalances;

  CryptoAccount({
    required this.userId,
    required this.fiatBalance,
    required this.totalCryptoValue,
    required this.cryptoBalances,
  });

  factory CryptoAccount.fromJson(Map<String, dynamic> json) {
    Map<String, CryptoBalance> balances = {};
    if (json['crypto_allocations'] != null) {
      json['crypto_allocations'].forEach((key, value) {
        balances[key] = CryptoBalance.fromJson(value);
      });
    }

    return CryptoAccount(
      userId: json['user_id'] ?? '',
      fiatBalance: (json['fiat_balance'] ?? 0.0).toDouble(),
      totalCryptoValue: (json['total_crypto_value'] ?? 0.0).toDouble(),
      cryptoBalances: balances,
    );
  }
}

class CryptoBalance {
  final double units;
  final double currentValue;
  final double avgPrice;

  CryptoBalance({
    required this.units,
    required this.currentValue,
    required this.avgPrice,
  });

  factory CryptoBalance.fromJson(Map<String, dynamic> json) {
    return CryptoBalance(
      units: (json['units'] ?? 0.0).toDouble(),
      currentValue: (json['current_value'] ?? 0.0).toDouble(),
      avgPrice: (json['avg_price'] ?? 0.0).toDouble(),
    );
  }
}

class CryptoPriceInfo {
  final String symbol;
  final double marketPrice;
  final double buyPrice;
  final double sellPrice;
  final double spreadPercent;
  final double priceChange24h;
  final double volatility;

  CryptoPriceInfo({
    required this.symbol,
    required this.marketPrice,
    required this.buyPrice,
    required this.sellPrice,
    required this.spreadPercent,
    required this.priceChange24h,
    required this.volatility,
  });

  factory CryptoPriceInfo.fromJson(Map<String, dynamic> json) {
    return CryptoPriceInfo(
      symbol: json['symbol'] ?? '',
      marketPrice: (json['market_price'] ?? 0.0).toDouble(),
      buyPrice: (json['buy_price'] ?? 0.0).toDouble(),
      sellPrice: (json['sell_price'] ?? 0.0).toDouble(),
      spreadPercent: (json['spread_percent'] ?? 0.0).toDouble(),
      priceChange24h: (json['price_change_24h'] ?? 0.0).toDouble(),
      volatility: (json['volatility'] ?? 0.0).toDouble(),
    );
  }
}

class TradeResult {
  final bool success;
  final String? error;
  final double? cryptoUnits;
  final double? fiatAmount;
  final double? price;
  final double? spread;
  final Map<String, dynamic>? newBalance;

  TradeResult({
    required this.success,
    this.error,
    this.cryptoUnits,
    this.fiatAmount,
    this.price,
    this.spread,
    this.newBalance,
  });

  factory TradeResult.fromJson(Map<String, dynamic> json) {
    return TradeResult(
      success: json['success'] ?? false,
      error: json['error'],
      cryptoUnits: (json['crypto_units'] ?? 0.0).toDouble(),
      fiatAmount: (json['fiat_amount'] ?? json['total_cost'] ?? 0.0).toDouble(),
      price: (json['price'] ?? 0.0).toDouble(),
      spread: (json['spread'] ?? 0.0).toDouble(),
      newBalance: json['new_balance'],
    );
  }
}