import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/account.dart';

class TransferProcessPage extends StatefulWidget {
  final BankAccount fromAccount;
  final String toAccount;
  final String amount;
  final String reference;
  final String bankCode;

  const TransferProcessPage({
    Key? key,
    required this.fromAccount,
    required this.toAccount,
    required this.amount,
    required this.reference,
    required this.bankCode,
  }) : super(key: key);

  @override
  _TransferProcessPageState createState() => _TransferProcessPageState();
}

class _TransferProcessPageState extends State<TransferProcessPage> {
  final ApiService _apiService = ApiService();
  String _currentStep = 'init';
  String _statusMessage = 'Подготовка перевода...';
  String? _consentId;
  String? _paymentId;
  bool _isSuccess = false;

  @override
  void initState() {
    super.initState();
    _startTransferProcess();
  }

  Future<void> _startTransferProcess() async {
    try {
      setState(() {
        _currentStep = 'requesting_consent';
        _statusMessage = 'Запрашиваем согласие на платёж...';
      });

      final result = await _apiService.makeTransfer(
        bankName: widget.bankCode,
        clientId: widget.fromAccount.clientId ?? 'team020-1',
        amount: widget.amount,
        fromAccount: widget.fromAccount.id,
        toAccount: widget.toAccount,
        reference: widget.reference,
      );

      if (result['success'] == true) {
        setState(() {
          _currentStep = 'completed';
          _statusMessage = 'Перевод выполнен успешно!';
          _consentId = result['consent_id'];
          _paymentId = result['payment_result']?['data']?['paymentId'];
          _isSuccess = true;
        });
      } else {
        setState(() {
          _currentStep = 'error';
          _statusMessage = 'Ошибка: ${result['error']}';
          _isSuccess = false;
        });
      }
    } catch (e) {
      setState(() {
        _currentStep = 'error';
        _statusMessage = 'Ошибка: $e';
        _isSuccess = false;
      });
    }
  }

  Widget _buildStepIcon(String step) {
    final isCurrent = _currentStep == step;
    final isCompleted = _getStepIndex(_currentStep) > _getStepIndex(step);

    if (isCompleted) {
      return Icon(Icons.check_circle, color: Colors.green);
    } else if (isCurrent) {
      return Container(
        width: 24,
        height: 24,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    } else {
      return Icon(Icons.radio_button_unchecked, color: Colors.grey);
    }
  }

  int _getStepIndex(String step) {
    switch (step) {
      case 'init': return 0;
      case 'requesting_consent': return 1;
      case 'executing_payment': return 2;
      case 'completed': return 3;
      case 'error': return 4;
      default: return 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text('Выполнение перевода'),
        backgroundColor: isDark ? Colors.grey[900] : Colors.blue[700],
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            Card(
              elevation: 2,
              color: isDark ? Colors.grey[800] : Colors.white,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Icon(Icons.arrow_upward, color: Colors.red),
                        SizedBox(width: 8),
                        Text('Списание: ${widget.fromAccount.accountNumber}'),
                      ],
                    ),
                    SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.arrow_downward, color: Colors.green),
                        SizedBox(width: 8),
                        Text('Зачисление: ${widget.toAccount}'),
                      ],
                    ),
                    SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.attach_money, color: Colors.blue),
                        SizedBox(width: 8),
                        Text('Сумма: ${widget.amount} ₽'),
                      ],
                    ),
                    if (widget.reference.isNotEmpty) ...[
                      SizedBox(height: 8),
                      Row(
                        children: [
                          Icon(Icons.description, color: Colors.grey),
                          SizedBox(width: 8),
                          Text('Назначение: ${widget.reference}'),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),

            SizedBox(height: 24),
            Card(
              elevation: 2,
              color: isDark ? Colors.grey[800] : Colors.white,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      children: [
                        _buildStepIcon('requesting_consent'),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Запрос согласия',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: isDark ? Colors.white : Colors.black,
                                ),
                              ),
                              Text(
                                _currentStep == 'requesting_consent'
                                    ? 'Отправляем запрос в банк...'
                                    : 'Согласие получено',
                                style: TextStyle(
                                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 16),
                    Row(
                      children: [
                        _buildStepIcon('executing_payment'),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Выполнение платежа',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: isDark ? Colors.white : Colors.black,
                                ),
                              ),
                              Text(
                                _currentStep == 'executing_payment'
                                    ? 'Выполняем перевод средств...'
                                    : _currentStep == 'completed'
                                    ? 'Платёж выполнен'
                                    : 'Ожидание',
                                style: TextStyle(
                                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            SizedBox(height: 24),

            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: _isSuccess
                    ? Colors.green.withOpacity(0.1)
                    : _currentStep == 'error'
                    ? Colors.red.withOpacity(0.1)
                    : Colors.blue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: _isSuccess
                      ? Colors.green
                      : _currentStep == 'error'
                      ? Colors.red
                      : Colors.blue,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    _isSuccess
                        ? Icons.check_circle
                        : _currentStep == 'error'
                        ? Icons.error
                        : Icons.info,
                    color: _isSuccess
                        ? Colors.green
                        : _currentStep == 'error'
                        ? Colors.red
                        : Colors.blue,
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _statusMessage,
                      style: TextStyle(
                        color: isDark ? Colors.white : Colors.black,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            if (_consentId != null) ...[
              SizedBox(height: 16),
              Text(
                'ID согласия: $_consentId',
                style: TextStyle(
                  color: Colors.grey,
                  fontSize: 12,
                ),
              ),
            ],

            Spacer(),

            Container(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.pop(context);
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isSuccess ? Colors.green : Colors.blue,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: Text(
                  _isSuccess ? 'Готово' : 'Вернуться',
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
    );
  }
}