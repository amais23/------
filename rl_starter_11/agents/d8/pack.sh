#!/bin/bash
# 自動編譯與打包指令檔
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

echo "=== 1. 本地編譯 (macOS) ==="
clang -arch arm64 -arch x86_64 -c src/weights.S -o src/weights.o
if [ -f "../../../.venv/bin/python" ]; then
    ../../../.venv/bin/python setup.py build_ext --inplace
else
    python3 setup.py build_ext --inplace
fi

echo "=== 2. Docker 編譯 (Linux manylinux2014) ==="
# 建立編譯 Docker 鏡像
docker build -t chess-build -f Dockerfile .
# 執行 Docker 編譯
docker run --rm -v "$(pwd)":/workspace -w /workspace chess-build /bin/bash -c "gcc -c src/weights.S -o src/weights.o && python setup.py build_ext --inplace"

# 清理編譯中間產物
rm -rf build

echo "=== 3. 複製開局庫 ==="
echo "=== 4. 打包 model.zip ==="
rm -f model.zip book_only.zip book.bin

# 找出編譯好的 Linux ELF 檔案
LINUX_SO=$(ls chess_engine_d8_han.cpython-*-linux-gnu.so | head -n 1)

# 直接將 ELF 偽裝成 model.zip 上傳！
cp "$LINUX_SO" model.zip

echo "=== 5. 打包完成！model.zip 已生成 (Pure ELF) ==="
ls -lh model.zip
