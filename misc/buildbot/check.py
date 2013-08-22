import logging

from downward.reports.absolute import AbsoluteReport


class Check(object):
    """
    Compare the attribute values x and y of two runs and check whether
    *min_rel* <= y/x <= *max_rel*. Even if the check fails, only report the
    failure if the absolute difference is greater than *ignored_abs_diff*.
    """
    def __init__(self, attribute, min_rel=None, max_rel=None, ignored_abs_diff=0):
        self.attribute = attribute
        self.min_rel = min_rel
        self.max_rel = max_rel
        self.ignored_abs_diff = ignored_abs_diff

    def get_error(self, base, new):
        # We assume that no attributes are missing.
        val1 = base[self.attribute]
        val2 = new[self.attribute]
        if abs(val2 - val1) <= self.ignored_abs_diff or val1 == 0:
            return ''
        factor = val2 / float(val1)
        msg = self.attribute + ' | %(val2).2f / %(val1).2f = %(factor).2f' % locals()
        if self.min_rel and factor < self.min_rel:
            return msg + ' < %.2f' % self.min_rel
        if self.max_rel and factor > self.max_rel:
            return msg + ' > %.2f' % self.max_rel
        return ''


class RegressionCheckReport(AbsoluteReport):
    """
    Write a table with the regressions. If there are none, no table is generated
    and therefore no output file is written.
    """
    def __init__(self, baseline, checks, **kwargs):
        """
        *baseline* must be a global revision identifier.

        *checks must be an iterable of Check instances.*
        """
        AbsoluteReport.__init__(self, **kwargs)
        self.baseline = baseline
        self.checks = checks

    def get_markup(self):
        lines = []
        for (domain, problem), runs in self.problem_runs.items():
            if runs[0]['planner'] == self.baseline:
                base, new = runs
            else:
                new, base = runs
            for check in self.checks:
                error = check.get_error(base, new)
                if error:
                    lines.append('| %(domain)s:%(problem)s | %(error)s |' % locals())
        if lines:
            # Add header.
            lines.insert(0, '|| Task | Attribute | Error |')
        return '\n'.join(lines)

    def write(self):
        AbsoluteReport.write(self)
        markup = self.get_markup()
        if markup:
            print 'There has been a regression:'
            print
            print markup
            logging.critical('Regression found.')
