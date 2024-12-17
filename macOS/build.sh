#!/bin/bash

# shellcheck source=/dev/null
# shellcheck disable=SC2317  # 不在此函数中警告无法访问的命令

# 错误处理函数
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

Rerun() {
	SCRIPT_PATH=$(readlink -f "$0")
	if [[ ! -x "$0" ]]; then
		chmod +x "$0"
	fi
	exec "${SCRIPT_PATH}" "$@"
}

main() {
	file_check='wifi_crack_tool_mac.py'
	env_pathName='.venv'
	requirements_path='../requirements.txt'
	arg="$#"
	debug=false
	if [[ "${arg}" != 0 ]]; then
		# 将所有传入的参数存储到数组
		args=("$@")
		if [[ "${args[0]}" == 'debug' ]]; then
			debug=true
			args[0]="${args[1]}" || true
			# args[1]="${args[2]}" || true
		elif [[ "${args[0]}" == 'update' ]]; then
			if git stash && git pull -f && git stash pop; then
				echo "✅更新完成"
				Rerun "$@"
			else
				echo '⚠️更新失败!☹️'
				exit 1
			fi
		fi
		if [[ "${debug}" == 'true' ]]; then
			echo "⚙️传参个数: ${arg}"
			echo "⚙️传入的参数：${args[*]}"
		fi
	fi
	cd "$(dirname "${BASH_SOURCE[0]}")" || true
	filename=$(basename "${file_check}" .py)
	env_path="${env_pathName}/bin/activate"
	${debug} && echo "⚙️当前路径: $(pwd)"
	if [[ ! -f "./${file_check}" ]]; then
		echo "❌ ${file_check} 文件不存在! "
		echo '请进入到项目下执行本脚本!'
		exit 1
	fi
	PATH="${args[0]:-${PATH}}"
	${debug} && echo "${PATH}"
	# python="${args[1]:-$(command -v python)}"
	if [ -n "${VIRTUAL_ENV}" ]; then
	    ${debug} && echo "⚙️当前使用 Python 虚拟环境：${VIRTUAL_ENV}"
	else
	    echo "⚠️当前环境似乎未使用 Python 虚拟环境"
	    if [[ -f "${env_path}" ]]; then
				load_time=3
				echo "⚙️检测到当前目录存在默认虚拟环境"
				echo "⚙️${load_time}秒后自动加载..."
				echo "tips:若取消加载请输入n,并回车.如需要立刻加载则直接回车."
				read -r -t ${load_time} flag || true
				if [[ "${flag}" != 'n' ]]; then
		        source "${env_path}"
		    fi
		  else
		  	read -r -e -p "❓是否需要在当前目录创建虚拟环境?(Y/n)" flag
		    if [[ "${flag}" != 'n' ]]; then
		        python -m venv .venv
		        source "${env_path}"
		    fi
			fi
			unset flag
	fi
	# 检查 Python 环境是否安装了 pyobjc-framework-CoreWLAN 依赖
	if python -c "import CoreWLAN" &>/dev/null; then
	    ${debug} && echo "✅ pyobjc-framework-CoreWLAN 已安装。"
	else
	    echo "❌必要依赖未安装!即将尝试安装! "
	    if pip install -r "${requirements_path}"; then
	    	echo "✅依赖安装成功！"
	    else
	    	echo "❌依赖安装失败! 已退出..."
			  exit 1
			fi
	fi
	if [[ ${debug} != 'true' && -d "./dist/${filename}.app" ]]; then
		echo "⚙️检测到已构建应用,正在启动..."
		./dist/"${filename}".app/Contents/MacOS/"${filename}"
		exit
	fi
	${debug} && python --version
	fontPath=$(python -c "import pyfiglet, os; print(os.path.join(os.path.dirname(pyfiglet.__file__), 'fonts'))")
	${debug} && echo '⚙️开始构建'
	pyinstaller --onefile --windowed --add-data "${fontPath}:pyfiglet/fonts" --distpath ./dist --workpath ./build ./${file_check} -y
	exit_code=$?

	if [ "${exit_code}" -eq 0 ]; then
	  echo "✅构建成功！"
	else
	  echo "❌构建执行失败，请检查错误信息! "
	  echo "tips:第一个参数为debug,可得到更详细信息"
	  exit 1
	fi
	read -r -e -p "⚙️是否需要启动程序?(Y/n)" flag
	if [[ "${flag}" != 'n' ]]; then
			echo '⚙️启动中...'
      ./dist/"${filename}".app/Contents/MacOS/"${filename}"
  fi
}


main "$@"
exit 0







