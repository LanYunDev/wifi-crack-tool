#!/bin/bash

# 错误处理函数
# shellcheck disable=SC2317  # Don't warn about unreachable commands in this function
handle_error() {
  echo "脚本发生错误，正在退出..."
	exit 1
}

# 定义信号处理函数，用于响应 Ctrl+C
function handle_ctrl_c {
	echo ""
	echo "接收到 Ctrl+C，正在退出..."
	exit 0
}

function exit_execute {
	echo "进程被杀死"
	exit 0
}

# 设置信号处理程序，捕捉 SIGINT 信号（Ctrl+C）
trap handle_ctrl_c SIGINT

# 设置trap命令，捕捉SIGTERM信号，并调用exit_execute函数
trap exit_execute SIGTERM

# 设置错误处理函数
trap handle_error ERR

main() {
	file_check='wifi_crack_tool_mac.py'
	echo "当前路径: $(pwd)"
	if [[ ! -f "${file_check}" ]]; then
		echo "❌ ${file_check} 文件不存在! "
		echo '请进入到项目下执行本脚本!'
		exit 1
	fi
	PATH="${1:-$(echo $PATH)}"
	python="${2:-$(command -v python)}"
	if [[ -d "./dist/test.app" ]]; then
		echo "检测到已构建应用,正在启动..."
		./dist/test.app/Contents/MacOS/test
		exit
	fi
	echo "$(python --version)"
	fontPath=$(python -c "import pyfiglet, os; print(os.path.join(os.path.dirname(pyfiglet.__file__), 'fonts'))")
	echo '⚙️开始构建'
	pyinstaller --onefile --windowed --add-data "${fontPath}/fonts/big.flf:pyfiglet/fonts" --distpath dist --workpath build test.py -y
	if [ $? -eq 0 ]; then
	  echo "✅构建成功！"
	else
	  echo "❌构建执行失败，请检查错误信息！"
	fi
	read -r -e -p "⚙️是否需要启动?(Y/n)" flag
	if [[ "${flag}" != 'n' ]]; then
      ./dist/test.app/Contents/MacOS/test
  fi
}


main "$@"
exit 0







