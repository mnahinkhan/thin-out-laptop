#/usr/bin/env bash

# Backup test-zone-current/test_data.txt.seagate in case something goes wrong
if [ -f test-zone-current/test_data.txt.seagate ]; then
    cp test-zone-current/test_data.txt.seagate test-zone-current/test_data.txt.seagate.bak
fi

# Restore this file at the end of the test, even if this script fails
trap "mv test-zone-current/test_data.txt.seagate.bak test-zone-current/test_data.txt.seagate" EXIT

# See if test-zone-current/test_data.txt.seagate can be recovered
if seagate download test-zone-current/test_data.txt; then
    # Check if test-zone-current/test_data.txt exists
    if [ -f test-zone-current/test_data.txt ]; then
        echo "Successfully recovered test-zone-current/test_data.txt"
    else
        echo "Failed to recover test-zone-current/test_data.txt"
        exit 1
    fi
else
    echo "Failed to download test_data.txt"
    exit 1
fi

# Make sure the seagate file does not exist anymore
if [ -f test-zone-current/test_data.txt.seagate ]; then
    echo "test-zone-current/test_data.txt.seagate still exists"
    exit 1
fi

# Test passed, so remove the downloaded file and restore the backed up seagate file
rm test-zone-current/test_data.txt
# mv test-zone-current/test_data.txt.seagate.bak test-zone-current/test_data.txt.seagate

# Now we test the new implementation

# Create a new file in test-zone-new
echo "This is a test file" > test-zone-new/test_data.txt

# Now run seagate evict on it, make sure the file disappears and is replaced by the seagate file
if seagate evict test-zone-new/test_data.txt; then
    # Check if test-zone-new/test_data.txt.seagate exists
    if [ -f test-zone-new/test_data.txt.seagate ]; then
        echo "Successfully evicted test-zone-new/test_data.txt"
    else
        echo "Failed to evict test-zone-new/test_data.txt"
        exit 1
    fi
else
    echo "Failed to evict test-zone-new/test_data.txt"
    exit 1
fi

# Make sure the original file does not exist anymore
if [ -f test-zone-new/test_data.txt ]; then
    echo "test-zone-new/test_data.txt still exists"
    exit 1
fi

# Now run seagate download on the seagate file, make sure the file reappears
if seagate download test-zone-new/test_data.txt; then
    # Check if test-zone-new/test_data.txt exists
    if [ -f test-zone-new/test_data.txt ]; then
        echo "Successfully recovered test-zone-new/test_data.txt"
    else
        echo "Failed to recover test-zone-new/test_data.txt"
        exit 1
    fi
else
    echo "Failed to download test-zone-new/test_data.txt"
    exit 1
fi

# Make sure the seagate file does not exist anymore
if [ -f test-zone-new/test_data.txt.seagate ]; then
    echo "test-zone-new/test_data.txt.seagate still exists"
    exit 1
fi

# Make sure the restored file contains the correct data
if [ "$(cat test-zone-new/test_data.txt)" != "This is a test file" ]; then
    echo "test-zone-new/test_data.txt does not contain the correct data"
    exit 1
fi


echo "Test passed, hooray!"