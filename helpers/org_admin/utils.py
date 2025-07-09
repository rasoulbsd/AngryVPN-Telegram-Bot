def get_user_credentials(effective_message):
    lines = []
    payment_receipt = None
    credentials = {}
    if effective_message.text:
        payment_receipt = effective_message.text.split('-------------------------')[1]
        lines = effective_message.text.splitlines()
    elif effective_message.caption:
        if effective_message.document:
            payment_receipt = effective_message.document.file_id
        elif effective_message.photo:
            payment_receipt = effective_message.photo[0].file_id
        lines = effective_message.caption.splitlines()
    credentials['payment_receipt'] = payment_receipt
    if lines and lines[0] == 'Payment':
        is_new_user = True
    else:
        is_new_user = False
    credentials['is_new_user'] = is_new_user
    for line in lines:
        if 'user_id' in line:
            credentials['user_id'] = int(line.split(':')[1])
        elif 'org' in line:
            credentials['org_name'] = line.split(':')[1]
        elif 'currency' in line:
            credentials['currency'] = line.split(':')[1]
        elif 'Plan' in line:
            credentials['plan'] = line.split(':')[1]
        elif 'pay_amount' in line:
            credentials['pay_amount'] = line.split(':')[1]
        elif 'discount' in line:
            credentials['discount'] = line.split(':')[1]
    return credentials 