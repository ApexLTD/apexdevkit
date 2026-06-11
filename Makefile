approve:
	find tests -type f -name '*_actual.*' -exec sh -c \
	'mv "$$0" "$${0%_actual.*}.$${0##*.}"' {} \;
