from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from smtplib import SMTP
import alerters
import settings


"""
Create any alerter you want here. The function will be invoked from trigger_alerts.
Three arguments will be passed, all of them tuples: alert and two lists of metrics.

alert: the tuple specified in your settings:
    alert[0]: The matched substring of the anomalous metric
    alert[1]: the name of the strategy being used to alert
    alert[2]: The timeout of the alert that was triggered
new_metrics: information about the newly reported anomalies themselves
    new_metrics[i][0]: the anomalous value
    new_metrics[i][1]: The full name of the anomalous metric
notified_metrics: information about already reported anomalies
    like above but alerters should only include these at no additional cost
    (attention and otherwise) to receivers
"""


def alert_smtp(alert, new_metrics, notified_metrics):

    # For backwards compatibility
    if '@' in alert[1]:
        sender = settings.ALERT_SENDER
        recipient = alert[1]
    else:
        sender = settings.SMTP_OPTS['sender']
        recipients = settings.SMTP_OPTS['recipients'][alert[0]]

    # Backwards compatibility
    if type(recipients) is str:
        recipients = [recipients]

    body = []
    if len(new_metrics) == 1:
        metric = new_metrics[0]
        subject = '[skyline alert] ' + metric[1]
        link = '%s/render/?width=588&height=308&target=%s' % (settings.GRAPHITE_HOST, metric[1])
        body.append('Anomalous value: %s <br> Next alert in: %s seconds <a href="%s"><img src="%s"/></a>' %
                    (metric[0], alert[2], link, link))
    else:
        subject = '[skyline alert] %d anomalous metrics' % len(new_metrics)
        for metric in new_metrics:
            link = '%s/render/?width=588&height=308&target=%s' % (settings.GRAPHITE_HOST, metric[1])
            body.append('<a href="%s">%s</a> = %s' % (link, metric[1, metric[0]]))

    if notified_metrics:
        subject += ' (%d already reported)' % len(notified_metrics)
        body.append('<br>Already reported metrics')
        for metric in notified_metrics:
            link = '%s/render/?width=588&height=308&target=%s' % (settings.GRAPHITE_HOST, metric[1])
            body.append('<a href="%s">%s</a> = %s' % (link, metric[1, metric[0]]))

    for recipient in recipients:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        msg.attach(MIMEText('<br>'.join(body), 'html'))
        s = SMTP('127.0.0.1')
        s.sendmail(sender, recipient, msg.as_string())
        s.quit()


def alert_pagerduty(alert, new_metrics, notified_metrics):
    import pygerduty
    pager = pygerduty.PagerDuty(settings.PAGERDUTY_OPTS['subdomain'], settings.PAGERDUTY_OPTS['auth_token'])
    for metric in new_metrics:
        pager.trigger_incident(settings.PAGERDUTY_OPTS['key'], "Anomalous metric: %s (value: %s)" % (metric[1], metric[0]))


def alert_hipchat(alert, new_metrics, notified_metrics):
    import hipchat
    hipster = hipchat.HipChat(token=settings.HIPCHAT_OPTS['auth_token'])
    rooms = settings.HIPCHAT_OPTS['rooms'][alert[0]]

    for metric in new_metrics:
        link = '%s/render/?width=588&height=308&target=%s' % (settings.GRAPHITE_HOST, metric[1])

        for room in rooms:
            hipster.method('rooms/message', method='POST', parameters={'room_id': room, 'from': 'Skyline', 'color': settings.HIPCHAT_OPTS['color'], 'message': 'Anomaly: <a href="%s">%s</a> : %s' % (link, metric[1], metric[0])})


def trigger_alerts(alert, new_metrics, notified_metrics):

    if '@' in alert[1]:
        strategy = 'alert_smtp'
    else:
        strategy = 'alert_' + alert[1]

    getattr(alerters, strategy)(alert, new_metrics, notified_metrics)
