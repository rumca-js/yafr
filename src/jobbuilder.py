from .jobhandlers import *


def job2handler(connection, job, table_name):
    if job.job == BackgroundJob.JOB_PROCESS_SOURCE:
        return ProcessSourceJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_CLEANUP:
        return CleanupJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_LINK_UPDATE_DATA:
        return UpdateLinkJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_LINK_RESET_DATA:
        return ResetLinkJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_LINK_ADD:
        return AddLinkJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL:
        return DownloadSocialDataJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD:
        return LinkDownloadJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC:
        return LinkAudioDownloadJobHandler(connection = connection, job=job, table_name = table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO:
        return LinkVideoDownloadJobHandler(connection = connection, job=job, table_name = table_name)
