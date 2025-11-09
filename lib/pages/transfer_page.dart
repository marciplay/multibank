import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/account.dart';
import 'transfer_process_page.dart';

class TransferPage extends StatefulWidget {
  final List<BankAccount> accounts;

  const TransferPage({Key? key, required this.accounts}) : super(key: key);

  @override
  _TransferPageState createState() => _TransferPageState();
}

class _TransferPageState extends State<TransferPage> {
  final ApiService _apiService = ApiService();
  final _formKey = GlobalKey<FormState>();

  BankAccount? _selectedFromAccount;
  String? _selectedToAccount;
  final _amountController = TextEditingController();
  final _referenceController = TextEditingController();
  final _customAccountController = TextEditingController();

  bool _isLoading = false;
  bool _useCustomAccount = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme
        .of(context)
        .brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text('Перевод между счетами'),
        backgroundColor: isDark ? Colors.grey[900] : Colors.blue[700],
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: Container(
          padding: EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Счёт списания
                Text(
                  'Счёт списания',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: isDark ? Colors.white : Colors.black,
                  ),
                ),
                SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    color: isDark ? Colors.grey[800] : Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: DropdownButton<BankAccount>(
                    value: _selectedFromAccount,
                    isExpanded: true,
                    underline: SizedBox(),
                    items: widget.accounts.map((account) {
                      return DropdownMenuItem(
                        value: account,
                        child: Row(
                          children: [
                            Icon(Icons.account_balance, size: 20),
                            SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(account.bankName),
                                  Text(
                                    '${account.balance.toStringAsFixed(
                                        2)} ${account.currency}',
                                    style: TextStyle(fontSize: 12),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                    onChanged: (account) {
                      setState(() {
                        _selectedFromAccount = account;
                      });
                    },
                  ),
                ),

                SizedBox(height: 20),

                // Счёт зачисления
                Row(
                  children: [
                    Text(
                      'Счёт зачисления',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: isDark ? Colors.white : Colors.black,
                      ),
                    ),
                    Spacer(),
                    Text('Мои счета'),
                    Switch(
                      value: _useCustomAccount,
                      onChanged: (value) {
                        setState(() {
                          _useCustomAccount = value;
                          _selectedToAccount = null;
                          _customAccountController.clear();
                        });
                      },
                    ),
                    Text('Другой счёт'),
                  ],
                ),
                SizedBox(height: 8),

                if (!_useCustomAccount)
                  Container(
                    decoration: BoxDecoration(
                      color: isDark ? Colors.grey[800] : Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey[300]!),
                    ),
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: DropdownButton<String>(
                      value: _selectedToAccount,
                      isExpanded: true,
                      underline: SizedBox(),
                      items: widget.accounts
                          .where((account) => account != _selectedFromAccount)
                          .map((account) {
                        return DropdownMenuItem(
                          value: account.id,
                          child: Row(
                            children: [
                              Icon(Icons.account_balance, size: 20),
                              SizedBox(width: 8),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(account.bankName),
                                    Text(
                                      account.accountNumber,
                                      style: TextStyle(fontSize: 12),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                      onChanged: (accountId) {
                        setState(() {
                          _selectedToAccount = accountId;
                        });
                      },
                    ),
                  )
                else
                  TextFormField(
                    controller: _customAccountController,
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: isDark ? Colors.grey[800] : Colors.white,
                      border: OutlineInputBorder(),
                      hintText: 'Введите номер счёта получателя',
                      prefixIcon: Icon(Icons.credit_card),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Введите номер счёта';
                      }
                      return null;
                    },
                  ),

                SizedBox(height: 20),

                // Сумма перевода
                Text(
                  'Сумма перевода',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: isDark ? Colors.white : Colors.black,
                  ),
                ),
                SizedBox(height: 8),
                TextFormField(
                  controller: _amountController,
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: isDark ? Colors.grey[800] : Colors.white,
                    border: OutlineInputBorder(),
                    labelText: 'Сумма',
                    prefixIcon: Icon(Icons.attach_money),
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Введите сумму';
                    }
                    if (double.tryParse(value) == null) {
                      return 'Введите корректную сумму';
                    }
                    if (_selectedFromAccount != null &&
                        double.parse(value) > _selectedFromAccount!.balance) {
                      return 'Недостаточно средств';
                    }
                    return null;
                  },
                ),

                SizedBox(height: 16),

                // Назначение платежа
                TextFormField(
                  controller: _referenceController,
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: isDark ? Colors.grey[800] : Colors.white,
                    border: OutlineInputBorder(),
                    labelText: 'Назначение платежа',
                    prefixIcon: Icon(Icons.description),
                  ),
                ),

                Spacer(),

                // Кнопка перевода
                Container(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _makeTransfer,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: _isLoading
                        ? SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                        : Text(
                      'Выполнить перевод',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _makeTransfer() async {
    print('🔄 Начало процесса перевода');

    if (!_formKey.currentState!.validate()) {
      print('❌ Форма не валидна');
      return;
    }

    final fromAccount = _selectedFromAccount;
    if (fromAccount == null) {
      print('❌ Не выбран счёт списания');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Выберите счёт списания')),
      );
      return;
    }

    final toAccount = _useCustomAccount
        ? _customAccountController.text
        : _selectedToAccount;

    if (toAccount == null || toAccount.isEmpty) {
      print('❌ Не выбран счёт зачисления');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Выберите счёт зачисления')),
      );
      return;
    }

    print('✅ Данные для перевода:');
    print('   От: ${fromAccount.accountNumber}');
    print('   Кому: $toAccount');
    print('   Сумма: ${_amountController.text}');
    print('   Назначение: ${_referenceController.text}');

    // Определяем банк для перевода (из счета списания)
    final bankCode = _getBankCode(fromAccount.bankName);

    // Переходим на страницу процесса перевода
    print('🔄 Переход на TransferProcessPage');
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) =>
            TransferProcessPage(
              fromAccount: fromAccount,
              toAccount: toAccount,
              amount: _amountController.text,
              reference: _referenceController.text.isEmpty
                  ? "Перевод между счетами"
                  : _referenceController.text,
              bankCode: bankCode, // Передаем код банка
            ),
      ),
    ).then((_) {
      print('🔙 Вернулись с TransferProcessPage');
    });
  }

  String _getBankCode(String bankName) {
    switch (bankName) {
      case 'Волга Банк':
        return 'vbank';
      case 'Альфа Банк':
        return 'abank';
      case 'Сити Банк':
        return 'sbank';
      default:
        return 'vbank';
    }
  }
}