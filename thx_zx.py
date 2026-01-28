import os
import json
import base64

# 设置目标目录
folder_path = r'C:\ths\同花顺\微信用户xxx\custom_block' # 目录替换成自己的

# 遍历目录下所有 .json 文件
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    if not os.path.isfile(file_path):
        continue
    if not filename.isdigit():
        continue
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取 ln 并解码
        ln_b64 = data.get("ln", "")
        if ln_b64:
            # 补齐 Base64 padding（有时会被省略）
            missing_padding = len(ln_b64) % 4
            if missing_padding:
                ln_b64 += '=' * (4 - missing_padding)
            try:
                decoded_bytes = base64.b64decode(ln_b64)
                ln_text = decoded_bytes.decode('gbk')
            except Exception as e:
                ln_text = f"[解码失败: {e}]"
        else:
            ln_text = ""

        # 提取 context 中的股票代码
        context = data.get("context", "")
        stock_codes = []
        if context:
            # 取第一个 ',' 之前的部分（股票代码部分）
            code_part = context.split(',')[0]
            # 按 '|' 分割，过滤空字符串
            stock_codes = [code.strip() for code in code_part.split('|') if code.strip()]
        if len(stock_codes) > 0: 
            # 输出结果
            print(f"文件: {filename}")
            print(f"  ln (GBK): {ln_text}")
            print(f"  股票代码: {stock_codes}")
            print("-" * 50)
        
        

    except Exception as e:
        print(f"处理文件 {filename} 时出错: {e}")
