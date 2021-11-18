import matplotlib.pyplot as plt
import sql

from datetime import datetime
INSERT_DELAY = 300

def make_plot(tuples):
    dates_full  = []
    temp = []
    hum = []
    for line in tuples:
        dates_full.append(line[0])
        temp.append(line[1])
        hum.append(line[2])
    fig, (ax1, ax2) = plt.subplots(2, sharex=True)
    ax1.plot(dates_full, temp)
    ax2.plot(dates_full, hum)
    plt.xticks(dates_full,rotation=90)
    ax1.set_title('Temperature')
    ax2.set_title('Humidite')
    plt.ylim(bottom=0)
    plt.ylim(top=100)
    return fig, (ax1,ax2)

def make_recent_plot(table_name, limit):
    tuples = sql.get_last_records(table_name,limit)
    fig,(ax1,ax2) = make_plot(tuples)
    fig.suptitle('{0} dernières mesures de {1}'.format(limit,table_name))
    plt.savefig('graphs/{}_last.png'.format(table_name),dpi=70,bbox_inches='tight')


def make_recent_step_plots(table_name, step, limit):
    tuples = sql.get_last_step_records(table_name,step,limit)
    fig, (ax1, ax2) = make_plot(tuples)
    fig.suptitle('{0} dernières heures de {1}'.format(round(limit*step*INSERT_DELAY/3600),table_name))
    plt.savefig('graphs/{0}_last_step_{1}.png'.format(table_name,step),dpi=100,bbox_inches='tight')

def make_period_plot(table_name, date_sup, date_inf, limit):
    date_sup_t = datetime.strptime(date_sup, '%Y-%m-%d %H:%M:%S')
    date_inf_t = datetime.strptime(date_inf, '%Y-%m-%d %H:%M:%S')
    diff_s = (date_sup_t - date_inf_t).total_seconds()
    step = round(diff_s / INSERT_DELAY /limit)

    tuples = sql.get_step_records(table_name,date_sup,step,limit)
    fig, (ax1, ax2) = make_plot(tuples)
    m, d, h = s_to_m_d_h(limit*step*INSERT_DELAY)
    fig.suptitle('{0}m, {1}d, {2}h de {3}'.format(m,d,h,table_name))
    plt.savefig('graphs/{0}_period_{1}.png'.format(table_name,date_sup),dpi=100,bbox_inches='tight')

def s_to_m_d_h(seconds):
    hours = seconds // 3600

    days = hours // 24
    hours -= days * 24

    months = days // 30
    days -= months * 30

    return int(months), int(days), int(hours)
