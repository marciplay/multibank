import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/account.dart';
import '../models/payment.dart';
import '../models/crypto.dart';

class ApiService {
  static const String bankBaseUrl = "http://10.0.2.2:8000";
  static const String cryptoBaseUrl = "http://10.0.2.2:8002";

  // Все методы для всех банков
  Future<List<String>> getConnectedBanks() async {
    try {
      final response = await http.get(
        Uri.parse('$bankBaseUrl/banks/connections'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) {
          return data.cast<String>();
        }
      }
      return ['vbank', 'abank', 'sbank'];
    } catch (e) {
      print('Ошибка получения списка банков: $e');
      return ['vbank', 'abank', 'sbank'];
    }
  }

  // Получить счета для конкретного банка
  Future<List<BankAccount>> getBankAccounts(String bankName, String clientId) async {
    try {
      print('Запрашиваем счета из $bankName для клиента $clientId');
      final response = await http.get(
        Uri.parse('$bankBaseUrl/banks/$bankName/accounts?client_id=$clientId'),
      );

      if (response.statusCode == 200) {
        final dynamic responseData = json.decode(response.body);
        print('Получены данные от $bankName');

        // Преобразуем в Map<String, dynamic>
        if (responseData is Map) {
          final Map<String, dynamic> data = _convertToStringKeyMap(responseData);
          return _extractAccountsFromBackend(data, bankName);
        } else {
          return _getDemoBankData(bankName);
        }
      } else {
        print('Ошибка API $bankName: ${response.statusCode}');
        return _getDemoBankData(bankName);
      }
    } catch (e) {
      print('Ошибка подключения к $bankName: $e');
      return _getDemoBankData(bankName);
    }
  }

  // Пакетное получение счетов из нескольких банков
  Future<List<BankAccount>> getBulkAccounts(Map<String, List<String>> bankClients) async {
    try {
      final List<Map<String, dynamic>> requestBody = [];

      bankClients.forEach((bankName, clientIds) {
        requestBody.add({
          'bank_name': bankName,
          'client_ids': clientIds,
        });
      });

      final response = await http.post(
        Uri.parse('$bankBaseUrl/banks/accounts_bulk'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(requestBody),
      );

      if (response.statusCode == 200) {
        final dynamic responseData = json.decode(response.body);
        List<BankAccount> allAccounts = [];

        if (responseData is Map) {
          final Map<String, dynamic> data = _convertToStringKeyMap(responseData);
          data.forEach((bankName, accountsData) {
            if (accountsData is Map) {
              final Map<String, dynamic> accountsMap = _convertToStringKeyMap(accountsData);
              final accounts = _extractAccountsFromBackend(accountsMap, bankName);
              allAccounts.addAll(accounts);
            }
          });
        }

        return allAccounts;
      } else {
        throw Exception('Ошибка пакетного запроса: ${response.statusCode}');
      }
    } catch (e) {
      print('Ошибка пакетного запроса: $e');
      // Возвращаем демо-данные для всех банков
      List<BankAccount> allAccounts = [];
      bankClients.forEach((bankName, clientIds) {
        allAccounts.addAll(_getDemoBankData(bankName));
      });
      return allAccounts;
    }
  }


  // Запрос согласия на платеж
  Future<PaymentConsentResponse> requestPaymentConsent({
    required String bankName,
    required String clientId,
    required String amount,
    required String debtorAccount,
    required String creditorAccount,
    String? creditorName,
    String? reference,
  }) async {
    try {
      final Map<String, dynamic> body = {
        'requesting_bank': "team020",
        'client_id': clientId,
        'consent_type': "single_use",
        'amount': amount,
        'debtor_account': debtorAccount,
        'creditor_account': creditorAccount,
        'creditor_name': creditorName,
        'reference': reference ?? "Перевод между счетами",
      };

      final response = await http.post(
        Uri.parse('$bankBaseUrl/banks/$bankName/request-payment-consent'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(body),
      );

      if (response.statusCode == 200) {
        final dynamic jsonResponse = json.decode(response.body);
        final Map<String, dynamic> responseMap = _convertToStringKeyMap(jsonResponse);
        return PaymentConsentResponse.fromJson(responseMap);
      } else {
        throw Exception('Ошибка запроса согласия: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Не удалось запросить согласие: $e');
    }
  }

  // Выполнение платежа
  Future<Map<String, dynamic>> executePayment({
    required String bankName,
    required String clientId,
    required String consentId,
    required String amount,
    required String debtorAccount,
    required String creditorAccount,
    String? bankCode,
  }) async {
    try {
      final Map<String, dynamic> body = {
        'data': {
          'initiation': {
            'instructedAmount': {
              'amount': amount,
              'currency': 'RUB',
            },
            'debtorAccount': {
              'schemeName': 'RU.CBR.PAN',
              'identification': debtorAccount,
            },
            'creditorAccount': {
              'schemeName': 'RU.CBR.PAN',
              'identification': creditorAccount,
              if (bankCode != null) 'bank_code': bankCode,
            },
          },
        },
      };

      final uri = Uri.parse('$bankBaseUrl/payments/execute').replace(queryParameters: {
        'client_id': clientId,
        'consent_id': consentId,
        'bank_name': bankName,
      });

      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(body),
      );

      if (response.statusCode == 200) {
        final dynamic responseData = json.decode(response.body);
        return _convertToStringKeyMap(responseData);
      } else {
        throw Exception('Ошибка выполнения платежа: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Не удалось выполнить платёж: $e');
    }
  }

  Future<Map<String, dynamic>> makeTransfer({
    required String bankName,
    required String clientId,
    required String amount,
    required String fromAccount,
    required String toAccount,
    String? reference,
  }) async {
    try {

      final consentResponse = await requestPaymentConsent(
        bankName: bankName,
        clientId: clientId,
        amount: amount,
        debtorAccount: fromAccount,
        creditorAccount: toAccount,
        reference: reference,
      );


      await Future.delayed(Duration(seconds: 10));


      final paymentResult = await executePayment(
        bankName: bankName,
        clientId: clientId,
        consentId: consentResponse.consentId,
        amount: amount,
        debtorAccount: fromAccount,
        creditorAccount: toAccount,
      );

      return {
        'success': true,
        'consent_id': consentResponse.consentId,
        'payment_result': paymentResult,
      };
    } catch (e) {
      return {
        'success': false,
        'error': e.toString(),
      };
    }
  }

  //Крипта

  Future<CryptoAccount?> getCryptoPortfolio(String userId) async {
    try {
      final response = await http.get(
        Uri.parse('$cryptoBaseUrl/api/crypto/portfolio/$userId'),
      );

      if (response.statusCode == 200) {
        return CryptoAccount.fromJson(json.decode(response.body));
      }
      return _getDemoCryptoAccount(userId);
    } catch (e) {
      print(' Ошибка получения крипто-портфеля: $e');
      return _getDemoCryptoAccount(userId);
    }
  }

  Future<TradeResult> buyCrypto(String userId, String crypto, double amount) async {
    try {
      final response = await http.post(
        Uri.parse('$cryptoBaseUrl/api/crypto/buy'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'user_id': userId,
          'crypto': crypto,
          'amount': amount,
        }),
      );

      if (response.statusCode == 200) {
        return TradeResult.fromJson(json.decode(response.body));
      } else {
        return TradeResult(success: false, error: 'Ошибка сервера: ${response.statusCode}');
      }
    } catch (e) {
      print('Ошибка покупки криптовалюты: $e');
      return _getDemoTradeResult(crypto, amount, true);
    }
  }

  Future<TradeResult> sellCrypto(String userId, String crypto, double units) async {
    try {
      final response = await http.post(
        Uri.parse('$cryptoBaseUrl/api/crypto/sell'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'user_id': userId,
          'crypto': crypto,
          'units': units,
        }),
      );

      if (response.statusCode == 200) {
        return TradeResult.fromJson(json.decode(response.body));
      } else {
        return TradeResult(success: false, error: 'Ошибка сервера: ${response.statusCode}');
      }
    } catch (e) {
      print('Ошибка продажи криптовалюты: $e');
      return _getDemoTradeResult(crypto, units, false);
    }
  }

  Future<CryptoPriceInfo> getCryptoPrice(String crypto) async {
    try {
      final response = await http.get(
        Uri.parse('$cryptoBaseUrl/api/crypto/price-info/$crypto'),
      );

      if (response.statusCode == 200) {
        return CryptoPriceInfo.fromJson(json.decode(response.body));
      }
      return _getDemoCryptoPrice(crypto);
    } catch (e) {
      print('Ошибка получения цены криптовалюты: $e');
      return _getDemoCryptoPrice(crypto);
    }
  }

  Future<TradeResult> depositToCrypto(String userId, double amount) async {
    try {
      final response = await http.post(
        Uri.parse('$cryptoBaseUrl/api/crypto/deposit'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'user_id': userId,
          'amount': amount,
        }),
      );

      if (response.statusCode == 200) {
        return TradeResult.fromJson(json.decode(response.body));
      } else {
        return TradeResult(success: false, error: 'Ошибка депозита: ${response.statusCode}');
      }
    } catch (e) {
      print('Ошибка депозита в крипто-модуль: $e');
      return TradeResult(success: true, fiatAmount: amount);
    }
  }

  Future<TradeResult> withdrawFromCrypto(String userId, double amount) async {
    try {
      final response = await http.post(
        Uri.parse('$cryptoBaseUrl/api/crypto/withdraw'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'user_id': userId,
          'amount': amount,
        }),
      );

      if (response.statusCode == 200) {
        return TradeResult.fromJson(json.decode(response.body));
      } else {
        return TradeResult(success: false, error: 'Ошибка вывода: ${response.statusCode}');
      }
    } catch (e) {
      print('Ошибка вывода из крипто-модуля: $e');
      return TradeResult(success: true, fiatAmount: amount);
    }
  }

  Map<String, dynamic> _convertToStringKeyMap(dynamic data) {
    if (data is Map) {
      final Map<String, dynamic> result = {};
      data.forEach((key, value) {
        result[key.toString()] = value;
      });
      return result;
    }
    return {};
  }


  List<BankAccount> _extractAccountsFromBackend(Map<String, dynamic> backendData, String bankName) {
    List<BankAccount> accounts = [];

    if (backendData.isEmpty) {
      print('$bankName вернул пустые данные');
      return _getDemoBankData(bankName);
    }
    backendData.forEach((clientId, clientAccounts) {
      if (clientAccounts is List && clientAccounts.isNotEmpty) {
        for (var accountData in clientAccounts) {
          final Map<String, dynamic> accountMap = _convertToStringKeyMap(accountData);
          double balance = _extractBalance(accountMap);
          List<Transaction> transactions = _extractTransactions(accountMap, bankName);
          String accountNumber = _extractAccountNumber(accountMap);
          final account = BankAccount(
            id: accountMap['id'] ?? 'unknown',
            balance: balance,
            currency: accountMap['currency'] ?? 'RUB',
            bankName: _formatBankName(bankName),
            accountNumber: accountNumber,
            clientId: clientId,
            transactions: transactions,
          );
          accounts.add(account);
        }
      }
    });
    return accounts.isEmpty ? _getDemoBankData(bankName) : accounts;
  }

  String _formatBankName(String bankCode) {
    switch (bankCode) {
      case 'vbank': return 'V Bанk';
      case 'abank': return 'А Bанk';
      case 'sbank': return 'S Bank';
      default: return bankCode;
    }
  }

  double _extractBalance(Map<String, dynamic> accountData) {
    try {
      if (accountData['balances'] != null && accountData['balances'] is List) {
        final List<dynamic> balances = accountData['balances'];
        if (balances.isNotEmpty) {
          final balanceData = _convertToStringKeyMap(balances[0]);
          return double.tryParse(balanceData['amount']?['amount'] ?? '0.0') ?? 0.0;
        }
      }
      return 0.0;
    } catch (e) {
      print('Ошибка извлечения баланса: $e');
      return 0.0;
    }
  }

  List<Transaction> _extractTransactions(Map<String, dynamic> accountData, String bankName) {
    List<Transaction> transactions = [];

    try {
      if (accountData['transactions'] != null && accountData['transactions'] is List) {
        List<dynamic> transactionsData = accountData['transactions'];

        for (var txData in transactionsData) {
          try {
            final Map<String, dynamic> txMap = _convertToStringKeyMap(txData);
            final transaction = Transaction(
              id: txMap['transactionId'] ?? txMap['id'] ?? 'unknown',
              amount: _parseTransactionAmount(txMap),
              description: txMap['description'] ?? txMap['transactionInformation'] ?? 'Операция',
              date: _parseTransactionDate(txMap),
              category: txMap['category'] ?? 'Другое',
              bankName: _formatBankName(bankName),
            );
            transactions.add(transaction);
          } catch (e) {
            print('Ошибка парсинга транзакции: $e');
          }
        }
      }
    } catch (e) {
      print('Ошибка извлечения транзакций: $e');
    }

    print('Извлечено транзакций: ${transactions.length}');
    return transactions;
  }

  // Демо-данные банков
  List<BankAccount> _getDemoBankData(String bankName) {
    print('🔄 Используем демо-данные для $bankName');

    final formattedName = _formatBankName(bankName);

    switch (bankName) {
      case 'vbank':
        return [
          BankAccount(
            id: 'vbank-001',
            balance: 152430.75,
            currency: 'RUB',
            bankName: formattedName,
            accountNumber: '**** 4582',
            clientId: 'team020-1',
            transactions: _getDemoTransactions(formattedName),
          ),
        ];

      case 'abank':
        return [
          BankAccount(
            id: 'abank-001',
            balance: 87520.30,
            currency: 'RUB',
            bankName: formattedName,
            accountNumber: '**** 3398',
            clientId: 'team020-1',
            transactions: _getDemoTransactions(formattedName),
          ),
        ];

      case 'sbank':
        return [
          BankAccount(
            id: 'sbank-001',
            balance: 254800.50,
            currency: 'RUB',
            bankName: formattedName,
            accountNumber: '**** 7821',
            clientId: 'team020-1',
            transactions: _getDemoTransactions(formattedName),
          ),
        ];

      default:
        return [
          BankAccount(
            id: '$bankName-001',
            balance: 100000.0,
            currency: 'RUB',
            bankName: formattedName,
            accountNumber: '**** 0001',
            clientId: 'team020-1',
            transactions: _getDemoTransactions(formattedName),
          ),
        ];
    }
  }

  List<Transaction> _getDemoTransactions(String bankName) {
    return [
      Transaction(
        id: 'txn-001',
        amount: -25000.0,
        description: 'Перевод средств',
        date: DateTime.now().subtract(Duration(days: 1)),
        category: 'Перевод',
        bankName: bankName,
      ),
      Transaction(
        id: 'txn-002',
        amount: 100000.0,
        description: 'Пополнение счета',
        date: DateTime.now().subtract(Duration(days: 2)),
        category: 'Пополнение',
        bankName: bankName,
      ),
    ];
  }

  CryptoAccount _getDemoCryptoAccount(String userId) {
    return CryptoAccount(
      userId: userId,
      fiatBalance: 5000.0,
      totalCryptoValue: 2500.0,
      cryptoBalances: {
        'BTC': CryptoBalance(units: 0.025, currentValue: 1625.0, avgPrice: 65000.0),
        'ETH': CryptoBalance(units: 0.25, currentValue: 875.0, avgPrice: 3500.0),
      },
    );
  }

  CryptoPriceInfo _getDemoCryptoPrice(String crypto) {
    return CryptoPriceInfo(
      symbol: crypto,
      marketPrice: crypto == 'BTC' ? 65000.0 : 3500.0,
      buyPrice: crypto == 'BTC' ? 65500.0 : 3525.0,
      sellPrice: crypto == 'BTC' ? 64500.0 : 3475.0,
      spreadPercent: 1.5,
      priceChange24h: crypto == 'BTC' ? 2.3 : -1.2,
      volatility: 15.5,
    );
  }

  TradeResult _getDemoTradeResult(String crypto, double amount, bool isBuy) {
    final price = crypto == 'BTC' ? 65000.0 : 3500.0;

    if (isBuy) {
      return TradeResult(
        success: true,
        cryptoUnits: amount / price,
        fiatAmount: amount,
        price: price,
      );
    } else {
      return TradeResult(
        success: true,
        cryptoUnits: amount,
        fiatAmount: amount * price,
        price: price,
      );
    }
  }

  double _parseTransactionAmount(Map<String, dynamic> txData) {
    try {
      if (txData['amount'] != null) {
        if (txData['amount'] is String) {
          return double.tryParse(txData['amount']) ?? 0.0;
        } else if (txData['amount'] is Map) {
          final amountMap = _convertToStringKeyMap(txData['amount']);
          return double.tryParse(amountMap['amount'] ?? '0.0') ?? 0.0;
        }
      }
      return 0.0;
    } catch (e) {
      return 0.0;
    }
  }

  DateTime _parseTransactionDate(Map<String, dynamic> txData) {
    try {
      if (txData['date'] != null) {
        return DateTime.parse(txData['date']);
      }
      if (txData['bookingDate'] != null) {
        return DateTime.parse(txData['bookingDate']);
      }
      return DateTime.now();
    } catch (e) {
      return DateTime.now();
    }
  }

  String _extractAccountNumber(Map<String, dynamic> accountData) {
    try {
      return accountData['accountNumber'] ??
          accountData['identification'] ??
          accountData['number'] ??
          _formatAccountNumber(accountData['id'] ?? 'unknown');
    } catch (e) {
      return _formatAccountNumber(accountData['id'] ?? 'unknown');
    }
  }

  String _formatAccountNumber(String accountId) {
    if (accountId.startsWith('acc-')) {
      return '**** ${accountId.substring(4)}';
    }
    return '**** ${accountId.substring(accountId.length - 4)}';
  }

  Future<List<BankAccount>> getAccounts(String bankName) async {
    return await getBankAccounts(bankName, 'team020-1');
  }

  Future<List<BankAccount>> getBankAccountsOld(String bankName) async {
    return await getBankAccounts(bankName, 'team020-1');
  }
}