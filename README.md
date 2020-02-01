# jblib
## Author: Justin Bard

This module was written to minimize the need to write the functions I use often.

INSTALL:  ` python3 -m pip install jblibaws `

---
The source code can be viewed here: [https://github.com/ANamelessDrake/jblib](https://github.com/ANamelessDrake/jblib)

More of my projects can be found here: [http://justbard.com](http://justbard.com)

---

` from jblib import cd `
```
    class cd()
            
        Example: 
            with cd(directory):
                print (os.getcwd()) 

            print (os.getcwd()) ## Back at the originating directory on exit
```

---
` from jblib import hilight `
```
    class hilight(string).color(highlight=True, bold=True)

    EXAMPLE:
        print (hilight("Hello World").red(bold=True))

        Or you could make an object:
            text = hilight("Bar")

            print ("Foo "+text.blue())

        To return the original string:
            print (text.string)
    
    COLORS:
        red
        green
        yellow
        blue
        purple
        teal
        white

    FUN FACTS:
        * This class is loosely based off the very first bit of python code I ever wrote. It was initially created while teaching myself python. 
        * This module was intentionally misspelled to shorten the keystrokes needed during use. 
```

---
` from jblib import convert_module `
```
    Module to convert various data
            
            def convert_time_from_seconds(seconds_given)
                Converts a seconds into minutes, hours and days. 
            
            def IP2Int(ip)
                Converts a IPv4 address to a interger - This is useful to store IP addresses in databases
            
            def Int2IP(ipnum)
                Converts a interger back to an IPv4 address

            def urlcode(url, encode=False)
                Wrapper for urllib.parse.quote and urllib.parse.unquote.
                From urllib docs - Replace special characters in string using the %xx escape. Letters, digits, and the characters '_.-' are never quoted. By default, this function is intended for quoting the path section of URL. 
                - https://docs.python.org/3.1/library/urllib.parse.html?highlight=urllib#urllib.parse.quote
```

---
` from jblib import HTMLgen `
```
        Basic HTML generator
        02/09/2019

        class HTMLgen(head=False, tail=False, lang="en", docType="html")

        FUNCTIONS:
            title(self, title, scripts=None, css=None)
            body.add(content)
            tag(tag, content=False, close=True, cssclass=None)
            image(src, alt=None, srcset=None, height=None, width=None, style=None, cssclass=None)
            br() <-- Returns a </ br> tag
            div(cssclass) <-- Not yet implemented 
            table() -- Class Object
                table.add_row()
                table.produce_table()

        EXAMPLE:
            page = HTMLgen(True, True)
            page.title("This is the page Title", scripts="foo.js bar.js", css="styles.css nav.css")
            page.body.add(page.image("images/frontpage.jpg", width="100%"))
            page.body.add(page.tag("h1", "This is a header line"))
            page.body.add("This is another line")

            ## Creating a table
            test_table = HTMLgen.table()
            test_table.add_row(["column data 1", "column data 2", "column data 3"])
            test_table.add_row(["column data 4", "column data 5", "column data 6"])

            ## And finally we add the table to the rest of the page
            page.body.add(test_table.produce_table())


            page.return_html()

            ```
                <!DOCTYPE html>
                <html lang="en>
                    <head>
                        <title>This is the page Title</title>
                        <link rel="stylesheet" href="styles.css">
                        <link rel="stylesheet" href="nav.css">
                        <script src="foo.js"></script>
                        <script src="bar.js"></script>
                    </head>
                <body>
                    <img src="images/frontpage.jpg" width="100%">
                    <h1>This is a header line</h1>
                    This is another line
                   	<table>
                        <tr>
                            <td>column data 1</td><td>column data 2</td><td>column data 3</td>
                        </tr>
                        <tr>
                            <td>column data 4</td><td>column data 5</td><td>column data 6</td>
                        </tr>

                    </table>

                </body>
                </html>
            ```
```

---
` from jblib import progress_bar `
```
    Progress Bar
    02/25/2019
    
    FUNCTIONS:
        progress_bar(progress, barLength=50, text_field="Progress")

    EXAMPLE:
        counter = 0
        for i in range(100):
            counter += 1
            i = counter/100
            progress_bar(i, 50)
            sleep(0.1)

    Progress: [#########################-------------------------] 50.0%
```

---
` from jblib import StreamToLogger `
```
    DESCRIPTION:
        Fake file-like stream object that redirects writes to a logger instance.
        
    CLASS:
        StreamToLogger(object)
    EXAMPLE:
        if log_enabled: ## If true, all standard output and standard error to the console will be disabled
            # create logger
            logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%Y%m%d %H:%M:%S', filename=log_file)
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)

            logger.propagate = False
            fh = logging.FileHandler(log_file, "a")
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter(fmt='%(asctime)s - %(message)s', datefmt='%Y%m%d %H:%M:%S')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            keep_fds = [fh.stream.fileno()]

            stdout_logger = logging.getLogger('STDOUT')
            sl = StreamToLogger(stdout_logger, logging.INFO)
            sys.stdout = sl

            stderr_logger = logging.getLogger('STDERR')
            sle = StreamToLogger(stderr_logger, logging.ERROR)
            sys.stderr = sle
```
---
` from jblib import build_date_array `
```
    Build Date Arrays
    02/27/2019

    FUNCTIONS:
        build_date_array(days=1, start_date=str(datetime.date.today()), date_format='%Y-%m-%d', mon=True, tues=True, wed=True, thur=True, fri=True, sat=True, sun=True, weekend=True):

    EXAMPLE:
        dates = build_date_array(days=7, weekend=False)
        dates
            ['2019-02-27', '2019-02-28', '2019-03-01', '2019-03-02', '2019-03-03', '2019-03-05', '2019-03-06']
```