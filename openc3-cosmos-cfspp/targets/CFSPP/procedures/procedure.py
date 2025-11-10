# Script Runner test script
cmd("CFSPP EXAMPLE")
wait_check("CFSPP STATUS BOOL == 'FALSE'", 5)
