#!/bin/bash


main() {
	if ! command -v timeout; then
		if command -v brew; then
			brew install coreutils
		else
			function timeout() { perl -e 'alarm shift; exec @ARGV' "$@"; }
		fi
	fi
	args=("$@")
	timeout "${args[0]}" networksetup -setairportnetwork "${args[1]}" "${args[2]}" "${args[3]}"

}


main "$@"
exit 0







