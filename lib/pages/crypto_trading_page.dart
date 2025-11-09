import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/crypto.dart';

class CryptoTradingPage extends StatefulWidget {
  final String userId;

  const CryptoTradingPage({Key? key, required this.userId}) : super(key: key);

  @override
  _CryptoTradingPageState createState() => _CryptoTradingPageState();
}

class _CryptoTradingPageState extends State<CryptoTradingPage> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  late TabController _tabController;

  CryptoAccount? _cryptoAccount;
  CryptoPriceInfo? _btcPrice;
  CryptoPriceInfo? _ethPrice;
  bool _isLoading = true;

  final _buyAmountController = TextEditingController();
  final _sellAmountController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final portfolio = await _apiService.getCryptoPortfolio(widget.userId);
      final btcPrice = await _apiService.getCryptoPrice('BTC');
      final ethPrice = await _apiService.getCryptoPrice('ETH');

      setState(() {
        _cryptoAccount = portfolio;
        _btcPrice = btcPrice;
        _ethPrice = ethPrice;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Крипто-трейдинг'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: 'Торговля'),
            Tab(text: 'Портфель'),
          ],
        ),
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : TabBarView(
        controller: _tabController,
        children: [
          _buildTradingTab(),
          _buildPortfolioTab(),
        ],
      ),
    );
  }

  Widget _buildTradingTab() {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          if (_btcPrice != null) _buildPriceCard(_btcPrice!),
          if (_ethPrice != null) _buildPriceCard(_ethPrice!),

          SizedBox(height: 20),

          _buildTradeCard(
            'Покупка BTC',
            _buyAmountController,
            'Купить',
            Colors.green,
                () => _buyCrypto('BTC', _buyAmountController.text),
          ),

          SizedBox(height: 16),

          // Продажа
          _buildTradeCard(
            'Продажа BTC',
            _sellAmountController,
            'Продать',
            Colors.red,
                () => _sellCrypto('BTC', _sellAmountController.text),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceCard(CryptoPriceInfo priceInfo) {
    final isPositive = priceInfo.priceChange24h >= 0;

    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              priceInfo.symbol,
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              '\$${priceInfo.marketPrice.toStringAsFixed(2)}',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 4),
            Row(
              children: [
                Icon(
                  isPositive ? Icons.arrow_upward : Icons.arrow_downward,
                  color: isPositive ? Colors.green : Colors.red,
                  size: 16,
                ),
                Text(
                  '${isPositive ? '+' : ''}${priceInfo.priceChange24h.toStringAsFixed(2)}%',
                  style: TextStyle(
                    color: isPositive ? Colors.green : Colors.red,
                  ),
                ),
                Spacer(),
                Text('Спред: ${priceInfo.spreadPercent.toStringAsFixed(2)}%'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTradeCard(String title, TextEditingController controller, String buttonText, Color color, VoidCallback onTap) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            TextField(
              controller: controller,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Сумма в USD',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 12),
            Container(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: onTap,
                style: ElevatedButton.styleFrom(backgroundColor: color),
                child: Text(buttonText),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPortfolioTab() {
    if (_cryptoAccount == null) {
      return Center(child: Text('Нет данных о портфеле'));
    }

    return Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                children: [
                  Text('Общий баланс', style: TextStyle(fontSize: 16)),
                  Text(
                    '\$${_cryptoAccount!.totalCryptoValue.toStringAsFixed(2)}',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Фиат: \$${_cryptoAccount!.fiatBalance.toStringAsFixed(2)}',
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),

          SizedBox(height: 16),

          Text('Мои активы', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 8),

          ..._cryptoAccount!.cryptoBalances.entries.map((entry) {
            final balance = entry.value;
            if (balance.units > 0) {
              return Card(
                child: ListTile(
                  title: Text(entry.key),
                  subtitle: Text('${balance.units.toStringAsFixed(6)} units'),
                  trailing: Text('\$${balance.currentValue.toStringAsFixed(2)}'),
                ),
              );
            } else {
              return SizedBox();
            }
          }).toList(),
        ],
      ),
    );
  }

  Future<void> _buyCrypto(String crypto, String amount) async {
    final double? amountValue = double.tryParse(amount);
    if (amountValue == null || amountValue <= 0) {
      _showError('Введите корректную сумму');
      return;
    }

    final result = await _apiService.buyCrypto(widget.userId, crypto, amountValue);

    if (result.success) {
      _showSuccess('Куплено ${result.cryptoUnits!.toStringAsFixed(6)} $crypto');
      _buyAmountController.clear();
      _loadData(); // Обновляем данные
    } else {
      _showError(result.error!);
    }
  }

  Future<void> _sellCrypto(String crypto, String units) async {
    final double? unitsValue = double.tryParse(units);
    if (unitsValue == null || unitsValue <= 0) {
      _showError('Введите корректное количество');
      return;
    }

    final result = await _apiService.sellCrypto(widget.userId, crypto, unitsValue);

    if (result.success) {
      _showSuccess('Продано $units $crypto за \$${result.fiatAmount!.toStringAsFixed(2)}');
      _sellAmountController.clear();
      _loadData(); // Обновляем данные
    } else {
      _showError(result.error!);
    }
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _showError(String error) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(error),
        backgroundColor: Colors.red,
      ),
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    _buyAmountController.dispose();
    _sellAmountController.dispose();
    super.dispose();
  }
}