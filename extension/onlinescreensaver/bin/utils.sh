##############################################################################
# Logs a message to a log file (or to console if LOGFILE is /dev/stderr)

logger () {
	MSG=$1

	# do nothing if logging is not enabled
	if [ "x1" != "x$LOGGING" ]; then
		return
	fi

	# if no logfile is specified, default to the console
	if [ -z "$LOGFILE" ]; then
		LOGFILE=/dev/stderr
	fi

	echo "$(date): $MSG" >> "$LOGFILE"
}


##############################################################################
# Retrieves the current time in seconds

currentTime () {
	date +%s
}


##############################################################################
# Asks powerd to wake the device from suspend after a number of seconds.
# Must be called while in the readyToSuspend state.
# arguments: $1 - amount of seconds to wake up in

set_rtc_wakeup () {
	lipc-set-prop -i com.lab126.powerd rtcWakeup "$1" 2>&1
	logger "rtcWakeup has been set to $1"
}


##############################################################################
# Waits for a number of seconds, even across suspend: whenever the device is
# about to suspend, an RTC wakeup is scheduled for the remaining time.
# arguments: $1 - time in seconds from now

wait_for () {
	ENDWAIT=$(( $(currentTime) + $1 ))
	REMAININGWAITTIME=$(( ENDWAIT - $(currentTime) ))
	logger "Starting to wait for timeout to expire: $1"

	while [ $REMAININGWAITTIME -gt 0 ]; do
		EVENT=$(lipc-wait-event -s "$REMAININGWAITTIME" com.lab126.powerd readyToSuspend,wakeupFromSuspend,resuming)
		REMAININGWAITTIME=$(( ENDWAIT - $(currentTime) ))
		logger "Received event: $EVENT"

		case "$EVENT" in
			readyToSuspend*)
				set_rtc_wakeup $REMAININGWAITTIME
			;;
			wakeupFromSuspend*|resuming*)
				logger "Finishing the wait"
				break
			;;
			*)
				logger "Ignored event: $EVENT"
			;;
		esac
	done

	logger "Wait finished"
}
