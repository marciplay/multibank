import 'crypto.dart';

class BankAccount {
  final String id;
  final double balance;
  final String currency;
  final String bankName;
  final String accountNumber;
  final String? clientId;
  final List<Transaction> transactions;
  final CryptoAccount? cryptoAccount;

  BankAccount({
    required this.id,
    required this.balance,
    required this.currency,
    required this.bankName,
    required this.accountNumber,
    this.clientId,
    required this.transactions,
    this.cryptoAccount,
  });

  factory BankAccount.fromJson(Map<String, dynamic> json) {
    return BankAccount(
      id: json['id'] ?? '',
      balance: (json['balance'] ?? 0.0).toDouble(),
      currency: json['currency'] ?? 'RUB',
      bankName: json['bankName'] ?? 'Банк',
      accountNumber: json['accountNumber'] ?? '',
      clientId: json['clientId'],
      transactions: (json['transactions'] as List? ?? [])
          .map((tx) => Transaction.fromJson(tx))
          .toList(),
      cryptoAccount: json['cryptoAccount'] != null
          ? CryptoAccount.fromJson(json['cryptoAccount'])
          : null,
    );
  }
}

class Transaction {
  final String id;
  final double amount;
  final String description;
  final DateTime date;
  final String category;
  final String bankName;

  Transaction({
    required this.id,
    required this.amount,
    required this.description,
    required this.date,
    required this.category,
    required this.bankName,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['transactionId'] ?? json['id'] ?? '',
      amount: (json['amount'] is Map
          ? double.tryParse(json['amount']['amount'] ?? '0.0') ?? 0.0
          : (json['amount'] ?? 0.0).toDouble()),
      description: json['transactionInformation'] ??
          json['description'] ?? 'Операция',
      date: DateTime.parse(json['bookingDate'] ??
          json['date'] ?? DateTime.now().toString()),
      category: json['category'] ?? 'Другое',
      bankName: json['bankName'] ?? 'Банк',
    );
  }
}