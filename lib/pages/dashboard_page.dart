// pages/dashboard_page.dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/account.dart';
import 'transfer_page.dart';
import '../models/crypto.dart';
import 'crypto_trading_page.dart';

class DashboardPage extends StatefulWidget {
  final VoidCallback? toggleTheme;
  final ThemeMode? themeMode;
  final String selectedAccount;

  const DashboardPage({
    Key? key,
    this.toggleTheme,
    this.themeMode,
    required this.selectedAccount,
  }) : super(key: key);

  @override
  _DashboardPageState createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final ApiService _apiService = ApiService();
  List<BankAccount> _accounts = [];
  List<Transaction> _transactions = [];
  bool _isLoading = false;
  bool _hasConnectedBank = false;
  int _selectedIndex = 0;

  // ДОБАВЬТЕ ЭТОТ МЕТОД
  String _getFormattedBankName(String bankCode) {
    switch (bankCode) {
      case 'vbank': return 'V Bank';
      case 'abank': return 'А Bанk';
      case 'sbank': return 'S Bank';
      default: return bankCode;
    }
  }

  @override
  void initState() {
    super.initState();
  }

  void _showBankSelection() {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          width: double.maxFinite,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFF667eea),
                Color(0xFF764ba2),
              ],
            ),
            borderRadius: BorderRadius.circular(24),
          ),
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '🏦 Выберите банк',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  'Подключитесь к банку для начала работы',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.8),
                    fontSize: 16,
                  ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 24),
                _buildBankOption('🏢 Волга Банк', Colors.blue, Icons.business, 'Надежность и стабильность', 'vbank'),
                _buildBankOption('🚀 Альфа Банк', Colors.red, Icons.rocket_launch, 'Инновации и технологии', 'abank'),
                _buildBankOption('🏙️ Сити Банк', Colors.green, Icons.location_city, 'Городские решения', 'sbank'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBankOption(String bankName, Color color, IconData icon, String description, String bankCode) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: ListTile(
        leading: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [color, color.withOpacity(0.7)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: Colors.white, size: 24),
        ),
        title: Text(
          bankName,
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        subtitle: Text(
          description,
          style: TextStyle(
            color: Colors.white.withOpacity(0.8),
          ),
        ),
        trailing: Icon(Icons.arrow_forward_ios_rounded, color: Colors.white, size: 16),
        onTap: () {
          Navigator.pop(context);
          _connectToBank(bankCode);
        },
      ),
    );
  }

  Future<void> _connectToBank(String bankCode) async {
    setState(() {
      _isLoading = true;
    });

    try {
      // Получаем счета для выбранного банка - передаем оба параметра
      final accounts = await _apiService.getBankAccounts(bankCode, widget.selectedAccount);

      // Собираем все транзакции из всех счетов
      List<Transaction> allTransactions = [];
      for (var account in accounts) {
        allTransactions.addAll(account.transactions);
      }

      setState(() {
        _accounts = accounts;
        _transactions = allTransactions;
        _hasConnectedBank = true;
        _isLoading = false;
      });

      final bankName = _getFormattedBankName(bankCode);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('$bankName успешно подключен!'),
          backgroundColor: Colors.green,
        ),
      );

    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      final bankName = _getFormattedBankName(bankCode);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Ошибка подключения к $bankName'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  double get _totalBalance {
    return _accounts.fold(0.0, (sum, account) => sum + account.balance);
  }

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  void _showFeatureComingSoon(String featureName) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.build_rounded, size: 60, color: Colors.blue),
              SizedBox(height: 16),
              Text(
                'Скоро будет!',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text(
                'Функция "$featureName" находится в разработке',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: Colors.grey[600]),
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: Text('Понятно'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? Color(0xFF121212) : Colors.grey[50],
      appBar: AppBar(
        title: Text('MultiBank'),
        backgroundColor: isDark ? Color(0xFF1E1E1E) : Colors.white,
        elevation: 0,
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode),
            onPressed: widget.toggleTheme,
            tooltip: isDark ? 'Светлая тема' : 'Темная тема',
          ),
        ],
      ),
      body: _isLoading
          ? _buildLoadingScreen()
          : _hasConnectedBank ? _buildDashboard() : _buildEmptyState(),
      floatingActionButton: _hasConnectedBank ? _buildFloatingActionButton() : null,
      bottomNavigationBar: _hasConnectedBank ? _buildBottomNavigationBar() : null,
    );
  }

  Widget _buildLoadingScreen() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 20),
          Text(
            'Подключаемся к банку...',
            style: TextStyle(fontSize: 16),
          ),
        ],
      ),
    );
  }

  Widget _buildFloatingActionButton() {
    return FloatingActionButton(
      onPressed: _showBankSelection,
      child: Icon(Icons.add_business_rounded),
      backgroundColor: Colors.blue,
      foregroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    );
  }

  Widget _buildBottomNavigationBar() {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(24),
          topRight: Radius.circular(24),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, -2),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(24),
          topRight: Radius.circular(24),
        ),
        child: BottomNavigationBar(
          items: const <BottomNavigationBarItem>[
            BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_rounded),
              label: 'Главная',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.account_balance_wallet_rounded),
              label: 'Счета',
            ),
          ],
          currentIndex: _selectedIndex,
          onTap: _onItemTapped,
          backgroundColor: isDark ? Color(0xFF1E1E1E) : Colors.white,
          selectedItemColor: Colors.blue,
          unselectedItemColor: isDark ? Colors.grey[400] : Colors.grey[600],
          showUnselectedLabels: true,
          type: BottomNavigationBarType.fixed,
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final size = MediaQuery.of(context).size;

    return SingleChildScrollView(
      child: Container(
        height: size.height,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.blue, Colors.purple],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.account_balance_wallet_rounded,
                size: 80,
                color: Colors.white,
              ),
            ),
            SizedBox(height: 40),

            Padding(
              padding: EdgeInsets.symmetric(horizontal: 40),
              child: Text(
                'Добро пожаловать в MultiBank!',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : Colors.black,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            SizedBox(height: 16),

            // Описание
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 40),
              child: Text(
                'Объединяем все ваши банки в одном приложении. '
                    'Начните с подключения вашего первого банка.',
                style: TextStyle(
                  fontSize: 16,
                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            SizedBox(height: 40),

            Container(
              width: size.width * 0.7,
              height: 60,
              child: ElevatedButton(
                onPressed: _showBankSelection,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  elevation: 4,
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.add_business_rounded, size: 24),
                    SizedBox(width: 12),
                    Text(
                      'Подключить первый банк',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDashboard() {
    final currentBank = _accounts.isNotEmpty ? _accounts.first.bankName : 'Банк';
    final isRealAPI = currentBank == 'КосмоБанк';
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return IndexedStack(
      index: _selectedIndex,
      children: [
        _buildHomeTab(currentBank, isRealAPI, isDark),
        _buildAccountsTab(isDark),
      ],
    );
  }

  Widget _buildHomeTab(String currentBank, bool isRealAPI, bool isDark) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: isRealAPI
                    ? [Color(0xFF667eea), Color(0xFF764ba2)]
                    : [Color(0xFF4facfe), Color(0xFF00f2fe)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 10,
                  offset: Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        isRealAPI ? Icons.rocket_launch : Icons.account_balance,
                        color: Colors.white,
                        size: 24,
                      ),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            currentBank,
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            'Аккаунт: ${widget.selectedAccount}',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.9),
                              fontSize: 14,
                            ),
                          ),
                          Text(
                            isRealAPI ? '🔗 Подключено к API' : '',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.9),
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: Icon(Icons.swap_horiz_rounded, color: Colors.white),
                      onPressed: _showBankSelection,
                    ),
                  ],
                ),
                SizedBox(height: 20),
                Text(
                  'Общий баланс',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.8),
                    fontSize: 16,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  '${_totalBalance.toStringAsFixed(2)} ₽',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),

          SizedBox(height: 24),

          Text(
            'Быстрые действия',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black,
            ),
          ),
          SizedBox(height: 16),
          GridView.count(
            shrinkWrap: true,
            physics: NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            childAspectRatio: 1.3,
            mainAxisSpacing: 16,
            crossAxisSpacing: 16,
            children: [
              _buildActionCard(
                'Крипто-трейдинг',
                Icons.currency_bitcoin_rounded,
                Colors.orange,
                    () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => CryptoTradingPage(
                        userId: 'user-${widget.selectedAccount}', // Используем выбранный аккаунт
                      ),
                    ),
                  );
                },
                isDark,
              ),

              _buildActionCard(
                'Переводы',
                Icons.swap_horiz_rounded,
                Colors.green,
                    () {
                  if (_accounts.isEmpty) {
                    print('Нет счетов для перевода');
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Сначала подключите банк'),
                        backgroundColor: Colors.orange,
                      ),
                    );
                  } else {
                    print('Переходим на страницу переводов');
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => TransferPage(accounts: _accounts),
                      ),
                    ).then((_) {
                      print('Вернулись со страницы переводов');
                    });
                  }
                },
                isDark,
              ),
              _buildActionCard(
                'Платежи',
                Icons.payment_rounded,
                Colors.blue,
                    () => _showFeatureComingSoon('Платежи'),
                isDark,
              ),
              _buildActionCard(
                'Аналитика',
                Icons.analytics_rounded,
                Colors.purple,
                    () => _showFeatureComingSoon('Аналитика'),
                isDark,
              ),
            ],
          ),

          SizedBox(height: 24),

          // Последние транзакции
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Последние операции',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : Colors.black,
                ),
              ),
              TextButton(
                onPressed: () => _showFeatureComingSoon('История операций'),
                child: Text('Все операции'),
              ),
            ],
          ),
          SizedBox(height: 16),
          ..._buildTransactionList(isDark),
        ],
      ),
    );
  }

  Widget _buildActionCard(String title, IconData icon, Color color, VoidCallback onTap, bool isDark) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      color: isDark ? Color(0xFF1E1E1E) : Colors.white,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [color, color.withOpacity(0.7)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: Colors.white, size: 24),
              ),
              SizedBox(height: 12),
              Text(
                title,
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: isDark ? Colors.white : Colors.black,
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAccountsTab(bool isDark) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          Text(
            'Мои счета',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black,
            ),
          ),
          SizedBox(height: 16),
          ..._accounts.map((account) => _buildAccountCard(account, isDark)).toList(),
        ],
      ),
    );
  }

  Widget _buildCryptoTab(bool isDark) {
    return _isLoading
        ? Center(child: CircularProgressIndicator())
        : Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          Card(
            elevation: 4,
            child: Padding(
              padding: EdgeInsets.all(20),
              child: Column(
                children: [
                  Text(
                    'Крипто-портфель',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 16),
                  FutureBuilder<CryptoAccount?>(
                    future: _apiService.getCryptoPortfolio('user-${_accounts.isNotEmpty ? _accounts.first.id : 'demo'}'),
                    builder: (context, snapshot) {
                      if (snapshot.hasData && snapshot.data != null) {
                        final portfolio = snapshot.data!;
                        return Column(
                          children: [
                            Text(
                              '\$${portfolio.totalCryptoValue.toStringAsFixed(2)}',
                              style: TextStyle(
                                fontSize: 32,
                                fontWeight: FontWeight.bold,
                                color: Colors.orange,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Фиат: \$${portfolio.fiatBalance.toStringAsFixed(2)}',
                              style: TextStyle(color: Colors.grey),
                            ),
                          ],
                        );
                      } else {
                        return Column(
                          children: [
                            Text(
                              '\$0.00',
                              style: TextStyle(
                                fontSize: 32,
                                fontWeight: FontWeight.bold,
                                color: Colors.orange,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Начните торговать криптовалютой',
                              style: TextStyle(color: Colors.grey),
                            ),
                          ],
                        );
                      }
                    },
                  ),
                ],
              ),
            ),
          ),

          SizedBox(height: 20),
          Container(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => CryptoTradingPage(
                      userId: 'user-${_accounts.isNotEmpty ? _accounts.first.id : 'demo'}',
                    ),
                  ),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text(
                'Перейти к трейдингу',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ),
          ),

          SizedBox(height: 20),

          FutureBuilder<CryptoPriceInfo>(
            future: _apiService.getCryptoPrice('BTC'),
            builder: (context, snapshot) {
              if (snapshot.hasData) {
                final btcPrice = snapshot.data!;
                return Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Icon(Icons.currency_bitcoin, color: Colors.orange),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('BTC/USD', style: TextStyle(fontWeight: FontWeight.bold)),
                              Text('\$${btcPrice.marketPrice.toStringAsFixed(2)}'),
                            ],
                          ),
                        ),
                        Text(
                          '${btcPrice.priceChange24h >= 0 ? '+' : ''}${btcPrice.priceChange24h.toStringAsFixed(2)}%',
                          style: TextStyle(
                            color: btcPrice.priceChange24h >= 0 ? Colors.green : Colors.red,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }
              return CircularProgressIndicator();
            },
          ),
        ],
      ),
    );
  }

  Widget _buildAccountCard(BankAccount account, bool isDark) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isDark
              ? [Color(0xFF2D2D2D), Color(0xFF1E1E1E)]
              : [Colors.white, Colors.grey[50]!],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: ListTile(
        contentPadding: EdgeInsets.all(16),
        leading: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [_getBankColor(account.bankName), _getBankColor(account.bankName).withOpacity(0.7)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Center(
            child: Text(
              account.bankName.substring(0, 1),
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
          ),
        ),
        title: Text(
          account.bankName,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: isDark ? Colors.white : Colors.black,
            fontSize: 16,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(account.accountNumber),
            SizedBox(height: 4),
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '${account.balance.toStringAsFixed(2)} ${account.currency}',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: isDark ? Colors.white : Colors.black,
              ),
            ),
            SizedBox(height: 4),
          ],
        ),
      ),
    );
  }

  List<Widget> _buildTransactionList(bool isDark) {
    if (_transactions.isEmpty) {
      return [
        Container(
          padding: EdgeInsets.all(40),
          child: Column(
            children: [
              Icon(
                Icons.receipt_long_rounded,
                size: 60,
                color: isDark ? Colors.grey[600] : Colors.grey[400],
              ),
              SizedBox(height: 16),
              Text(
                'Пока нет операций',
                style: TextStyle(
                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                  fontSize: 16,
                ),
              ),
            ],
          ),
        ),
      ];
    }

    return _transactions.take(5).map((transaction) => _buildTransactionItem(transaction, isDark)).toList();
  }

  Widget _buildTransactionItem(Transaction transaction, bool isDark) {
    final isExpense = transaction.amount < 0;
    final icon = isExpense ? Icons.arrow_upward_rounded : Icons.arrow_downward_rounded;
    final color = isExpense ? Colors.red : Colors.green;

    return Container(
      margin: EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: isDark ? Color(0xFF1E1E1E) : Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 6,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: ListTile(
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color, size: 20),
        ),
        title: Text(
          transaction.description,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: isDark ? Colors.white : Colors.black,
          ),
        ),
        subtitle: Text(
          '${transaction.date.day}.${transaction.date.month}.${transaction.date.year} • ${transaction.bankName}',
          style: TextStyle(
            color: isDark ? Colors.grey[400] : Colors.grey[600],
          ),
        ),
        trailing: Text(
          '${isExpense ? '-' : '+'}${transaction.amount.abs().toStringAsFixed(2)} ₽',
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
      ),
    );
  }

  Color _getBankColor(String bankName) {
    switch (bankName) {
      case 'АБанк': return Colors.purple[800]!;
      case 'ВБанк': return Colors.green[700]!;
      case 'СБанк': return Colors.orange[800]!;
      default: return Colors.blue;
    }
  }
}