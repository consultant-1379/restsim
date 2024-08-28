import datetime

def calculate_timezone_offset(utc_time, local_time):

    # Calculate the time difference between UTC and local time
    time_difference = local_time - utc_time
    total_seconds = time_difference.total_seconds()

    # Calculate the hours and minutes from the total seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)

    # Construct the timezone offset string in the format +/-HHMM
    offset = '{:0=+03d}{:0=02d}'.format(hours, minutes)

    return offset

def convert_epoch_range(epoch_start, epoch_end):

    local_start_time = datetime.datetime.fromtimestamp(epoch_start)
    local_end_time = datetime.datetime.fromtimestamp(epoch_end)

    utc_start_time = datetime.datetime.utcfromtimestamp(epoch_start)
    utc_end_time = datetime.datetime.utcfromtimestamp(epoch_end)

    start_offset = calculate_timezone_offset(utc_start_time, local_start_time)
    end_offset = calculate_timezone_offset(utc_end_time, local_end_time)

    dateTime = {
        'local_start_date' : local_start_time.strftime("%Y%m%d"),
        'local_end_date' : local_end_time.strftime("%Y%m%d"),
        'local_start_time' : local_start_time.strftime("%H%M"),
        'local_end_time' : local_end_time.strftime("%H%M"),
        'start_offset' : start_offset,
        'end_offset' : end_offset,

        'utc_start_date' : utc_start_time.strftime("%Y%m%d"),
        'utc_end_date' : utc_end_time.strftime("%Y%m%d"),
        'utc_start_time' : utc_start_time.strftime("%H%M"),
        'utc_end_time' : utc_end_time.strftime("%H%M")
    }

    return dateTime
