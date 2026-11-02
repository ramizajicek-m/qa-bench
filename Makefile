# The kit's own tests run on the gate host under its heavy-run lock (tools/remote_test.sh): they
# drive real browsers, and this machine's load must not decide a verdict. `test-here` is a quick local look.
test:
	tools/remote_test.sh

test-here:
	python3 -m pytest tests -q

.PHONY: test test-here
