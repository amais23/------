#!/bin/bash
# 自動編譯與打包指令檔
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

echo "=== 1. 本地編譯 (macOS) ==="
if [ -f "../../../.venv/bin/python" ]; then
    ../../../.venv/bin/python setup.py build_ext --inplace
else
    python3 setup.py build_ext --inplace
fi

echo "=== 2. Docker 編譯 (Linux manylinux2014) ==="
# 建立編譯 Docker 鏡像
docker build -t chess-build -f Dockerfile .
# 執行 Docker 編譯
docker run --rm -v "$(pwd)":/workspace -w /workspace chess-build python setup.py build_ext --inplace

# 清理編譯中間產物
rm -rf build

echo "=== 3. 複製開局庫 ==="
# 將指定的 Lichess 開局庫複製為 book.bin
cp ../../../Lichess_51_Books/Books/AlPhAbEtACeta.bin ./book.bin

echo "=== 4. 打包 model.zip ==="
rm -f model.zip
# 打包需要的檔案，排除 C++ 源碼以保持乾淨
zip -r model.zip agent.py model.py book.bin chess_engine*.so

echo "=== 打包完成！model.zip 已生成 ==="
ls -lh model.zip
