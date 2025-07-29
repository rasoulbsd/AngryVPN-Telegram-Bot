from telegram import Bot
from helpers.initial import get_secrets_config

# asda
(secrets, Config) = get_secrets_config()

TOKEN=secrets['BotAPI']
bot=Bot(token=TOKEN)

# 0 warning, -1 exceed
async def send_warning_message(db ,user_dict, status = 0):
    print(f"Sending message to {user_dict['user_id']}")

    if 'status' not in user_dict:
        user_dict['status'] = 1
        db.users.update_one({'user_id': user_dict['user_id']}, {"$set": {"status": user_dict['status']}})
    reply_text = f"آی‌دی شما: `{user_dict['user_id']}`"

    latest_transaction = db.payments.find_one(
        {'user_id': user_dict['user_id'], 'verified': True},
        sort=[('_id', -1)]
    )

    reply_text += "\n\n"
    # reply_text += "❌ اعتبار شما تمام شد! لطفا از طریق منو حسابتان را شارژ کنید. ❌" if status == -1 else "⚠️ اعتبار شما کمتر از ۵ گیگ است. لطفا سریعا حسابتان را شارژ نمایید. ⚠️"
    reply_text += "❌ اعتبار شما تمام شد! لطفا از طریق منو حسابتان را شارژ کنید. ❌" if status == -1 else "⚠️ شما بیشتر از ۸۵٪ بسته‌ی آخر خود را مصرف کرده‌اید. لطفا اعتبار حسابتان را بررسی کرده و در صورت نیاز شارژ کنید. ⚠️"
    reply_text += "\n"

    if latest_transaction['payment_type'] == 'rial':
        multiply_factor = 1000
    else:
        multiply_factor = 1

    reply_text += f"\nکیف پول: {user_dict['wallet']*multiply_factor:.2f} تومان"
    flag = False
    if user_dict['status'] != status:
        if status == -1 or status == 0:
            try:
                # print("UPDATED!!!")
                await bot.send_message(chat_id=user_dict['user_id'], text=reply_text)
                print(f"{user_dict['user_id']}: sent warning or exceed!")
                flag = True
            except Exception as e:
                print(e)
        user_dict['status'] = status
        db.users.update_one({'user_id': user_dict['user_id']}, {"$set": {"status": user_dict['status']}})

    return flag
