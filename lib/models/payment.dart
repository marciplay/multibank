class PaymentConsentRequest {
  final String requestingBank;
  final String clientId;
  final String consentType;
  final String amount;
  final String debtorAccount;
  final String creditorAccount;
  final String? creditorName;
  final String? reference;

  PaymentConsentRequest({
    required this.requestingBank,
    required this.clientId,
    this.consentType = "single_use",
    required this.amount,
    required this.debtorAccount,
    required this.creditorAccount,
    this.creditorName,
    this.reference,
  });

  Map<String, dynamic> toJson() {
    return {
      'requesting_bank': requestingBank,
      'client_id': clientId,
      'consent_type': consentType,
      'amount': amount,
      'debtor_account': debtorAccount,
      'creditor_account': creditorAccount,
      'creditor_name': creditorName,
      'reference': reference,
    };
  }
}

class PaymentConsentResponse {
  final String requestId;
  final String consentId;
  final String status;
  final String consentType;
  final bool autoApproved;
  final String? message;

  PaymentConsentResponse({
    required this.requestId,
    required this.consentId,
    required this.status,
    required this.consentType,
    required this.autoApproved,
    this.message,
  });

  factory PaymentConsentResponse.fromJson(Map<String, dynamic> json) {
    return PaymentConsentResponse(
      requestId: json['request_id'] ?? '',
      consentId: json['consent_id'] ?? '',
      status: json['status'] ?? '',
      consentType: json['consent_type'] ?? '',
      autoApproved: json['auto_approved'] ?? false,
      message: json['message'],
    );
  }
}

class PaymentExecutionRequest {
  final PaymentInitiation initiation;

  PaymentExecutionRequest({required this.initiation});

  Map<String, dynamic> toJson() {
    return {
      'data': {
        'initiation': initiation.toJson(),
      },
    };
  }
}

class PaymentInitiation {
  final Amount instructedAmount;
  final Account debtorAccount;
  final Account creditorAccount;

  PaymentInitiation({
    required this.instructedAmount,
    required this.debtorAccount,
    required this.creditorAccount,
  });

  Map<String, dynamic> toJson() {
    return {
      'instructedAmount': instructedAmount.toJson(),
      'debtorAccount': debtorAccount.toJson(),
      'creditorAccount': creditorAccount.toJson(),
    };
  }
}

class Amount {
  final String amount;
  final String currency;

  Amount({required this.amount, this.currency = "RUB"});

  Map<String, dynamic> toJson() {
    return {
      'amount': amount,
      'currency': currency,
    };
  }
}

class Account {
  final String schemeName;
  final String identification;

  Account({this.schemeName = "RU.CBR.PAN", required this.identification});

  Map<String, dynamic> toJson() {
    return {
      'schemeName': schemeName,
      'identification': identification,
    };
  }
}