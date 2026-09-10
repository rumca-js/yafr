from .jobhandlers import *


def job2handler(job):
    if job.job == BackgroundJob.JOB_PROCESS_SOURCE:
        return ProcessSourceJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_CLEANUP:
        return CleanupJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_LINK_UPDATE_DATA:
        return UpdateLinkJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_LINK_RESET_DATA:
        return ResetLinkJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_LINK_ADD:
        return AddLinkJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL:
        return DownloadSocialDataJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD:
        return LinkDownloadJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC:
        return LinkAudioDownloadJobHandler(connection = self.connection, job=job, table_name = self.table_name)
    elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO:
        return LinkVideoDownloadJobHandler(connection = self.connection, job=job, table_name = self.table_name)
