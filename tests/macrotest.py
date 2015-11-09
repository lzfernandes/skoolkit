# -*- coding: utf-8 -*-

ERROR_PREFIX = 'Error while parsing #{} macro'

class CommonSkoolMacroTest:
    def _test_invalid_reference_macro(self, macro):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format(macro)

        self._assert_error(writer, '#{}#(foo)'.format(macro), "No item name: #{}#(foo)".format(macro), prefix)
        self._assert_error(writer, '#{}(foo'.format(macro), "No closing bracket: (foo", prefix)

        return writer, prefix

    def _check_call(self, writer, params, *args):
        macro = '#CALL:test_call({})'.format(params)
        if writer.needs_cwd():
            cwd = '<cwd>'
            self.assertEqual(writer.expand(macro, cwd), writer.test_call(*((cwd,) + args)))
        else:
            self.assertEqual(writer.expand(macro), writer.test_call(*args))

    def test_macro_bug_invalid(self):
        self._test_invalid_reference_macro('BUG')

    def test_macro_call(self):
        writer = self._get_writer(warn=True)
        writer.test_call = self._test_call

        # All arguments given
        self._check_call(writer, '10,t,5', 10, 't', 5)

        # One argument omitted
        self._check_call(writer, '7,,test2', 7, None, 'test2')

        # Arithmetic expressions
        self._check_call(writer, '7+2*5,12-4/2,3**3', 17, 10, 27)
        self._check_call(writer, '6&3|5,7^5,4%2', 7, 2, 0)
        self._check_call(writer, '1<<4,16>>4', 16, 1, None)
        self._check_call(writer, '1 + 1, (3 + 5) / 2, 4 * (9 - 7)', 2, 4, 8)

        # Non-arithmetic Python expressions
        self._check_call(writer, '"a"+"b",None,sys.exit()', '"a"+"b"', 'None', 'sys.exit()')

        # No arguments
        writer.test_call_no_args = self._test_call_no_args
        output = writer.expand('#CALL:test_call_no_args()')
        self.assertEqual(output, 'OK')

        # No return value
        writer.test_call_no_retval = self._test_call_no_retval
        output = writer.expand('#CALL:test_call_no_retval(1,2)')
        self.assertEqual(output, '')

        # Unknown method
        method_name = 'nonexistent_method'
        output = writer.expand('#CALL:{0}(0)'.format(method_name))
        self.assertEqual(output, '')
        self.assertEqual(self.err.getvalue().split('\n')[0], 'WARNING: Unknown method name in #CALL macro: {0}'.format(method_name))

    def test_macro_call_invalid(self):
        writer = self._get_writer()
        writer.test_call = self._test_call
        writer.var = 'x'
        prefix = ERROR_PREFIX.format('CALL')

        self._assert_error(writer, '#CALL', 'No parameters', prefix)
        self._assert_error(writer, '#CALLtest_call(5,s)', 'Malformed macro: #CALLt...', prefix)
        self._assert_error(writer, '#CALL:(0)', 'No method name', prefix)
        self._assert_error(writer, '#CALL:var(0)', 'Uncallable method name: var', prefix)
        self._assert_error(writer, '#CALL:test_call', 'No argument list specified: #CALL:test_call', prefix)
        self._assert_error(writer, '#CALL:test_call(1,2', 'No closing bracket: (1,2', prefix)
        self._assert_error(writer, '#CALL:test_call(1)')
        self._assert_error(writer, '#CALL:test_call(1,2,3,4)')

    def test_macro_chr_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('CHR')

        self._assert_error(writer, '#CHR', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#CHRx', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#CHR()', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#CHR(x,y)', "Cannot parse integer 'x' in parameter string: 'x,y'", prefix)
        self._assert_error(writer, '#CHR(1,2)', "Too many parameters (expected 1): '1,2'", prefix)
        self._assert_error(writer, '#CHR(2 ...', 'No closing bracket: (2 ...', prefix)

    def test_macro_d(self):
        skool = '\n'.join((
            '@start',
            '',
            '; First routine',
            'c32768 RET',
            '',
            '; Second routine',
            'c32769 RET',
            '',
            'c32770 RET',
        ))
        writer = self._get_writer(skool=skool)

        # Decimal address
        output = writer.expand('#D32768')
        self.assertEqual(output, 'First routine')

        # Hexadecimal address
        output = writer.expand('#D$8001')
        self.assertEqual(output, 'Second routine')

        # Arithmetic expression
        output = writer.expand('#D($8000 + 2 * 3 - (10 + 5) / 3)')
        self.assertEqual(output, 'Second routine')

        # Adjacent characters
        self.assertEqual(writer.expand('1+#D32768+1'), '1+First routine+1')
        self.assertEqual(writer.expand('+1#D(32768)1+'), '+1First routine1+')

    def test_macro_d_invalid(self):
        skool = '@start\nc32770 RET'
        writer = self._get_writer(skool=skool)
        prefix = ERROR_PREFIX.format('D')

        self._assert_error(writer, '#D', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#Dx', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#D32770', 'Entry at 32770 has no description', prefix)
        self._assert_error(writer, '#D32771', 'Cannot determine description for non-existent entry at 32771', prefix)

    def test_macro_erefs_invalid(self):
        writer = self._get_writer(skool='@start\nc30005 JP 30004')
        prefix = ERROR_PREFIX.format('EREFS')

        self._assert_error(writer, '#EREFS', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#EREFSx', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#EREFS(0,1)', "Too many parameters (expected 1): '0,1'", prefix)
        self._assert_error(writer, '#EREFS30005', 'Entry point at 30005 has no referrers', prefix)

    def test_macro_eval(self):
        writer = self._get_writer()

        # Decimal
        self.assertEqual(writer.expand('#EVAL5'), '5')
        self.assertEqual(writer.expand('#EVAL(5 + 2 * (2 + 1) - ($13 - 1) / 3)'), '5')
        self.assertEqual(writer.expand('#EVAL5,10'), '5')
        self.assertEqual(writer.expand('#EVAL5,,5'), '00005')

        # Hexadecimal
        self.assertEqual(writer.expand('#EVAL10,16'), 'A')
        self.assertEqual(writer.expand('#EVAL(31 + 2 * (4 - 1) - ($11 + 1) / 3, 16)'), '1F')
        self.assertEqual(writer.expand('#EVAL10,16,2'), '0A')

        # Binary
        self.assertEqual(writer.expand('#EVAL10,2'), '1010')
        self.assertEqual(writer.expand('#EVAL(15 + 2 * (5 - 2) - ($10 + 2) / 3, 2)'), '1111')
        self.assertEqual(writer.expand('#EVAL16,2,8'), '00010000')

    def test_macro_eval_with_nested_eval_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL(1+#EVAL(23-7)/5)'), '4')

    def test_macro_eval_with_nested_for_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL(#FOR1,4(n,n,*))'), '24')

    def test_macro_eval_with_nested_foreach_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL(#FOREACH(1,2,3,4)(n,n,*))'), '24')

    def test_macro_eval_with_nested_if_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL(1+#IF(5>4)(10,20))'), '11')

    def test_macro_eval_with_nested_map_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#EVAL(#MAP5(0,1:1,5:10))'), '10')

    def test_macro_eval_with_nested_peek_macro(self):
        writer = self._get_writer(snapshot=(2, 1))
        self.assertEqual(writer.expand('#EVAL(#PEEK0+256*#PEEK1)'), '258')

    def test_macro_eval_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('EVAL')

        self._assert_error(writer, '#EVAL', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#EVALx', 'No parameters (expected 1)', prefix)
        self._assert_error(writer, '#EVAL(1,x)', "Cannot parse integer 'x' in parameter string: '1,x'", prefix)
        self._assert_error(writer, '#EVAL(1,,x)', "Cannot parse integer 'x' in parameter string: '1,,x'", prefix)
        self._assert_error(writer, '#EVAL(1,10,5,8)', "Too many parameters (expected 3): '1,10,5,8'", prefix)
        self._assert_error(writer, '#EVAL5,3', 'Invalid base (3): 5,3', prefix)

    def test_macro_fact_invalid(self):
        self._test_invalid_reference_macro('FACT')

    def test_macro_font_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FONT')

        self._test_invalid_image_macro(writer, '#FONT', 'No parameters (expected 1)', prefix)
        self._test_invalid_image_macro(writer, '#FONT:', 'No text parameter', prefix)
        self._test_invalid_image_macro(writer, '#FONT(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#FONT0,1,2,3,4,5', "Too many parameters (expected 4): '0,1,2,3,4,5'", prefix)
        self._test_invalid_image_macro(writer, '#FONT0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#FONT0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#FONT0(foo', 'No closing bracket: (foo', prefix)
        self._test_invalid_image_macro(writer, '#FONT:()0', 'Empty message: ()', prefix)
        self._test_invalid_image_macro(writer, '#FONT:[hi)0', 'No closing bracket: [hi)0', prefix)

    def test_macro_for(self):
        writer = self._get_writer()

        # Default step
        output = writer.expand('#FOR1,3(n,n)')
        self.assertEqual(output, '123')

        # Step
        output = writer.expand('#FOR1,5,2(n,n)')
        self.assertEqual(output, '135')

        # Brackets and commas in output
        output = writer.expand('(1)#FOR5,13,4//n/, (n)//')
        self.assertEqual(output, '(1), (5), (9), (13)')

        # Alternative delimiters
        for delim1, delim2 in (('[', ']'), ('{', '}')):
            output = writer.expand('1; #FOR4,10,3{}@n,@n; {}13'.format(delim1, delim2))
            self.assertEqual(output, '1; 4; 7; 10; 13')

        # Alternative separator
        output = writer.expand('1, #FOR4,10,3/|@n|@n, |/13')
        self.assertEqual(output, '1, 4, 7, 10, 13')

        # Arithmetic expression in 'start' parameter
        output = writer.expand('#FOR(10 - (20 + 7) / 3, 3)(n,n)')
        self.assertEqual(output, '123')

        # Arithmetic expression in 'stop' parameter
        output = writer.expand('#FOR(1, (5 + 1) / 2)(n,n)')
        self.assertEqual(output, '123')

        # Arithmetic expression in 'step' parameter
        output = writer.expand('#FOR(1, 13, 2 * (1 + 2))(n,[n])')
        self.assertEqual(output, '[1][7][13]')

    def test_macro_for_with_separator(self):
        writer = self._get_writer()

        # One value
        output = writer.expand('#FOR1,1($s,$s,+)')
        self.assertEqual(output, '1')

        # More than one value
        output = writer.expand('{ #FOR1,5(n,n, | ) }')
        self.assertEqual(output, '{ 1 | 2 | 3 | 4 | 5 }')

        # Separator contains a comma
        output = writer.expand('#FOR6,10//n/(n)/, //')
        self.assertEqual(output, '(6), (7), (8), (9), (10)')

    def test_macro_for_with_final_separator(self):
        writer = self._get_writer()

        # One value
        output = writer.expand('#FOR1,1($s,$s,+,-)')
        self.assertEqual(output, '1')

        # Two values
        output = writer.expand('#FOR1,2($s,$s,+,-)')
        self.assertEqual(output, '1-2')

        # Three values
        output = writer.expand('#FOR1,3//$s/$s/, / and //')
        self.assertEqual(output, '1, 2 and 3')

    def test_macro_for_with_nested_eval_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOR:0,2//m/{#EVAL(m+1)}//'), '{1}{2}{3}')

    def test_macro_for_with_nested_for_macro(self):
        writer = self._get_writer()
        output = writer.expand('#FOR1,3(&n,#FOR4,6[&m,&m.&n, ], )')
        self.assertEqual(output, '4.1 5.1 6.1 4.2 5.2 6.2 4.3 5.3 6.3')

    def test_macro_for_with_nested_foreach_macro(self):
        writer = self._get_writer()
        output = writer.expand('#FOR0,2//m/[#FOREACH(1,2,3)(n,m+n,-)]//')
        self.assertEqual(output, '[0+1-0+2-0+3][1+1-1+2-1+3][2+1-2+2-2+3]')

    def test_macro_for_with_nested_if_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOR:0,2//m/#IFm([m],{m})//'), '{0}[1][2]')
        self.assertEqual(writer.expand('#FOR0,2//m/#IF0([m],{m})//'), '{0}{1}{2}')

    def test_macro_for_with_nested_map_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOR:0,2//m/{#MAPm[,0:2,1:3,2:5]}//'), '{2}{3}{5}')

    def test_macro_for_with_nested_peek_macro(self):
        writer = self._get_writer(snapshot=(1, 2, 3))
        self.assertEqual(writer.expand('#FOR:0,2(m,{#PEEKm})'), '{1}{2}{3}')

    def test_macro_for_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FOR')

        self._assert_error(writer, '#FOR', 'No parameters (expected 2)', prefix)
        self._assert_error(writer, '#FOR:', 'No parameters (expected 2)', prefix)
        self._assert_error(writer, '#FOR0', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#FOR:0', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#FOR0,1', 'No variable name: 0,1', prefix)
        self._assert_error(writer, '#FOR:0,1', 'No variable name: 0,1', prefix)
        self._assert_error(writer, '#FOR0,1()', "No variable name: 0,1()", prefix)
        self._assert_error(writer, '#FOR:0,1()', "No variable name: 0,1()", prefix)
        self._assert_error(writer, '#FOR0,1(n,n', 'No closing bracket: (n,n', prefix)
        self._assert_error(writer, '#FOR:0,1(n,n', 'No closing bracket: (n,n', prefix)

    def test_macro_foreach(self):
        writer = self._get_writer()

        # No values
        output = writer.expand('#FOREACH()($s,$s)')
        self.assertEqual(output, '')

        # One value
        output = writer.expand('#FOREACH(a)($s,[$s])')
        self.assertEqual(output, '[a]')

        # Two values
        output = writer.expand('#FOREACH(a,b)($s,<$s>)')
        self.assertEqual(output, '<a><b>')

        # Three values
        output = writer.expand('#FOREACH(a,b,c)($s,*$s*)')
        self.assertEqual(output, '*a**b**c*')

        # Values containing commas
        output = writer.expand('#FOREACH//a,/b,/c//($s,$s)')
        self.assertEqual(output, 'a,b,c')

    def test_macro_foreach_with_separator(self):
        writer = self._get_writer()

        # No values
        output = writer.expand('#FOREACH()($s,$s,.)')
        self.assertEqual(output, '')

        # One value
        output = writer.expand('#FOREACH(a)($s,$s,.)')
        self.assertEqual(output, 'a')

        # Two values
        output = writer.expand('#FOREACH(a,b)($s,$s,+)')
        self.assertEqual(output, 'a+b')

        # Three values
        output = writer.expand('#FOREACH(a,b,c)($s,$s,-)')
        self.assertEqual(output, 'a-b-c')

        # Separator contains a comma
        output = writer.expand('#FOREACH(a,b,c)//$s/[$s]/, //')
        self.assertEqual(output, '[a], [b], [c]')

    def test_macro_foreach_with_final_separator(self):
        writer = self._get_writer()

        # No values
        output = writer.expand('#FOREACH()($s,$s,+,-)')
        self.assertEqual(output, '')

        # One value
        output = writer.expand('#FOREACH(a)($s,$s,+,-)')
        self.assertEqual(output, 'a')

        # Two values
        output = writer.expand('#FOREACH(a,b)($s,$s,+,-)')
        self.assertEqual(output, 'a-b')

        # Three values
        output = writer.expand('#FOREACH(a,b,c)//$s/$s/, / and //')
        self.assertEqual(output, 'a, b and c')

    def test_macro_foreach_with_nested_eval_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOREACH:(0,1,2)||n|#EVAL(n+1)|, ||'), '1, 2, 3')

    def test_macro_foreach_with_nested_for_macro(self):
        writer = self._get_writer()
        output = writer.expand('#FOREACH(0,1,2)||n|#FOR5,6//m/m.n/, //|, ||')
        self.assertEqual(output, '5.0, 6.0, 5.1, 6.1, 5.2, 6.2')

    def test_macro_foreach_with_nested_foreach_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOREACH(0,1)||n|#FOREACH(a,n)($s,[$s])|, ||'), '[a][0], [a][1]')

    def test_macro_foreach_with_nested_if_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOREACH:(0,1,2)//m/#IFm([m],{m})//'), '{0}[1][2]')
        self.assertEqual(writer.expand('#FOREACH(0,1,2)//m/#IF1([m],{m})//'), '[0][1][2]')

    def test_macro_foreach_with_nested_map_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOREACH:(0,1,2)||n|#MAPn(c,0:a,1:b)||'), 'abc')

    def test_macro_foreach_with_nested_peek_macro(self):
        writer = self._get_writer(snapshot=(1, 2, 3))
        self.assertEqual(writer.expand('#FOREACH:(0,1,2)(n,n+#PEEKn,+)'), '0+1+1+2+2+3')

    def test_macro_foreach_with_entry(self):
        skool = '\n'.join((
            '@start',
            'b30000 DEFB 1,2,3',
            '',
            'c30003 RET',
            '',
            'g30004 DEFB 0',
            '',
            's30005 DEFS 5',
            '',
            'c30010 RET',
            '',
            'b30011 DEFB 4,5,6',
            '',
            't30014 DEFM "Hey"',
            '',
            'u30017 DEFS 3',
            '',
            'w30020 DEFW 10000,20000',
            '',
            'c30024 RET',
        ))
        writer = self._get_writer(skool=skool)

        # All entries
        output = writer.expand('#FOREACH(ENTRY)||e|e|, ||')
        self.assertEqual(output, '30000, 30003, 30004, 30005, 30010, 30011, 30014, 30017, 30020, 30024')

        # Just code
        output = writer.expand('#FOREACH(ENTRYc)||e|e|, ||')
        self.assertEqual(output, '30003, 30010, 30024')

        # Code and text
        output = writer.expand('#FOREACH(ENTRYct)||e|e|, ||')
        self.assertEqual(output, '30003, 30010, 30014, 30024')

        # Everything but code and text
        output = writer.expand('#FOREACH(ENTRYbgsuw)||e|e|, ||')
        self.assertEqual(output, '30000, 30004, 30005, 30011, 30017, 30020')

        # Non-existent
        output = writer.expand('#FOREACH(ENTRYq)||e|e|, ||')
        self.assertEqual(output, '')

    def test_macro_foreach_with_eref(self):
        skool = '\n'.join((
            '@start',
            'c30000 CALL 30004',
            '',
            'c30003 LD A,B',
            ' 30004 LD B,C',
            '',
            'c30005 JP 30004',
            '',
            'c30008 JR 30004'
        ))
        writer = self._get_writer(skool=skool)

        cwd = ('asm',) if writer.needs_cwd() else ()
        exp_output = writer.expand(*(('#R30000, #R30005 and #R30008',) + cwd))
        macro_t = '#FOREACH[EREF{}]||addr|#Raddr|, | and ||'

        # Decimal address
        output = writer.expand(*((macro_t.format(30004),) + cwd))
        self.assertEqual(output, exp_output)

        # Hexadecimal address
        output = writer.expand(*((macro_t.format('$7534'),) + cwd))
        self.assertEqual(output, exp_output)

        # Arithmetic expression
        output = writer.expand(*((macro_t.format('30000 + 8 * (7 + 1) - ($79 - 1) / 2'),) + cwd))
        self.assertEqual(output, exp_output)

    def test_macro_foreach_with_eref_invalid(self):
        writer = self._get_writer(skool='')
        self.assertEqual(writer.expand('#FOREACH(EREFx)(n,n)'), 'EREFx')
        self.assertEqual(writer.expand('#FOREACH[EREF(x)](n,n)'), 'EREF(x)')

    def test_macro_foreach_with_ref(self):
        skool = '\n'.join((
            '@start',
            '; Used by the routines at 9, 89 and 789',
            'c00001 LD A,B',
            ' 00002 RET',
            '',
            'c00009 CALL 1',
            '',
            'c00089 CALL 1',
            '',
            'c00789 JP 2'
        ))
        writer = self._get_writer(skool=skool)

        cwd = ('asm',) if writer.needs_cwd() else ()
        exp_output = writer.expand(*(('#R9, #R89 and #R789',) + cwd))
        macro_t = '#FOREACH[REF{}]||addr|#Raddr|, | and ||'

        # Decimal address
        output = writer.expand(*((macro_t.format(1),) + cwd))
        self.assertEqual(output, exp_output)

        # Hexadecimal address
        output = writer.expand(*((macro_t.format('$0001'),) + cwd))
        self.assertEqual(output, exp_output)

        # Arithmetic expression
        output = writer.expand(*((macro_t.format('(1 + 5 * (2 + 3) - ($63 + 1) / 4)'),) + cwd))
        self.assertEqual(output, exp_output)

    def test_macro_foreach_with_ref_invalid(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#FOREACH(REFx)(n,n)'), 'REFx')
        self.assertEqual(writer.expand('#FOREACH[REF(x)](n,n)'), 'REF(x)')

    def test_macro_foreach_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('FOREACH')

        self._assert_error(writer, '#FOREACH', 'No values', prefix)
        self._assert_error(writer, '#FOREACH:', 'No values', prefix)
        self._assert_error(writer, '#FOREACH()', 'No variable name: ()', prefix)
        self._assert_error(writer, '#FOREACH:()', 'No variable name: ()', prefix)
        self._assert_error(writer, '#FOREACH()()', 'No variable name: ()()', prefix)
        self._assert_error(writer, '#FOREACH:()()', 'No variable name: ()()', prefix)
        self._assert_error(writer, '#FOREACH(a,b[$s,$s]', 'No closing bracket: (a,b[$s,$s]', prefix)
        self._assert_error(writer, '#FOREACH:(a,b[$s,$s]', 'No closing bracket: (a,b[$s,$s]', prefix)
        self._assert_error(writer, '#FOREACH(a,b)($s,$s', 'No closing bracket: ($s,$s', prefix)
        self._assert_error(writer, '#FOREACH:(a,b)($s,$s', 'No closing bracket: ($s,$s', prefix)
        self._assert_error(writer, '#FOREACH(REF$81A4)(n,n)', 'No entry at 33188: REF$81A4', prefix)
        self._assert_error(writer, '#FOREACH:(REF$81A4)(n,n)', 'No entry at 33188: REF$81A4', prefix)

    def test_macro_html_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('HTML')

        self._assert_error(writer, '#HTML', 'No text parameter', prefix)
        self._assert_error(writer, '#HTML:unterminated', 'No terminating delimiter: :unterminated', prefix)

    def test_macro_if(self):
        writer = self._get_writer()

        # Integers
        self.assertEqual(writer.expand('#IF1(Yes,No)'), 'Yes')
        self.assertEqual(writer.expand('#IF(0)(Yes,No)'), 'No')

        # Arithmetic expressions
        self.assertEqual(writer.expand('#IF(1+2*3+4/2)(On,Off)'), 'On')
        self.assertEqual(writer.expand('#IF(1+2*3-49/7)(On,Off)'), 'Off')
        self.assertEqual(writer.expand('#IF(2&5|1)(On,Off)'), 'On')
        self.assertEqual(writer.expand('#IF(7^7)(On,Off)'), 'Off')
        self.assertEqual(writer.expand('#IF(3%2)(On,Off)'), 'On')
        self.assertEqual(writer.expand('#IF(2>>2)(On,Off)'), 'Off')
        self.assertEqual(writer.expand('#IF(1<<2)(On,Off)'), 'On')

        # Equalities and inequalities
        self.assertEqual(writer.expand('#IF(0==0)||(True)|(False)||'), '(True)')
        self.assertEqual(writer.expand('#IF(0!=0)||(True)|(False)||'), '(False)')
        self.assertEqual(writer.expand('#IF(1<2)||(True)|(False)||'), '(True)')
        self.assertEqual(writer.expand('#IF(1>2)||(True)|(False)||'), '(False)')
        self.assertEqual(writer.expand('#IF(3<=4)||(True)|(False)||'), '(True)')
        self.assertEqual(writer.expand('#IF(3>=4)||(True)|(False)||'), '(False)')

        # Arithmetic expressions in equalities and inequalities
        self.assertEqual(writer.expand('#IF(1+2==6-3)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF(1+2!=6-3)||(Y)|(N)||'), '(N)')
        self.assertEqual(writer.expand('#IF(3*3<4**5)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF(3&3>4|5)||(Y)|(N)||'), '(N)')
        self.assertEqual(writer.expand('#IF(12/6<=12^4)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF(12%6>=12/4)||(Y)|(N)||'), '(N)')
        self.assertEqual(writer.expand('#IF(1<<3>16>>2)||(Y)|(N)||'), '(Y)')

        # Arithmetic expressions with brackets and spaces
        self.assertEqual(writer.expand('#IF(3+(2*6)/4>(9-3)/3)||(Y)|(N)||'), '(Y)')
        self.assertEqual(writer.expand('#IF( 3 + (2 * 6) / 4 < (9 - 3) / 3 )||(Y)|(N)||'), '(N)')

        # Arithmetic expressions with && and ||
        self.assertEqual(writer.expand('#IF(5>4&&2!=3)(T,F)'), 'T')
        self.assertEqual(writer.expand('#IF(4 > 5 || 3 < 3)(T,F)'), 'F')
        self.assertEqual(writer.expand('#IF(2==2&&4>5||3<4)(T,F)'), 'T')

        # Multi-line output strings
        self.assertEqual(writer.expand('#IF1(foo\nbar,baz\nqux)'), 'foo\nbar')
        self.assertEqual(writer.expand('#IF0(foo\nbar,baz\nqux)'), 'baz\nqux')

        # No 'false' parameter
        self.assertEqual(writer.expand('#IF1(aye)'), 'aye')
        self.assertEqual(writer.expand('#IF0(aye)'), '')
        self.assertEqual(writer.expand('#IF1()'), '')
        self.assertEqual(writer.expand('#IF0()'), '')

    def test_macro_if_with_nested_eval_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF(#EVAL(1+1)>1)(Y,N)'), 'Y')
        self.assertEqual(writer.expand('#IF(3<1)(#EVAL(2+2),#EVAL(3*3))'), '9')

    def test_macro_if_with_nested_for_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF(#FOR0,2(n,n,+))(Y,N)'), 'Y')
        self.assertEqual(writer.expand('#IF1(#FOR1,2(n,Y),N)'), 'YY')

    def test_macro_if_with_nested_foreach_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF(#FOREACH(0,1,2)(n,n,+))(Y,N)'), 'Y')
        self.assertEqual(writer.expand('#IF1(#FOREACH(1,2)(n,Y),N)'), 'YY')

    def test_macro_if_with_nested_if_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF(#IF(5>3)(2<1,1))(Y,N)'), 'N')
        self.assertEqual(writer.expand('#IF(5>3)(#IF1||T,F|Y,N||)'), 'T')

    def test_macro_if_with_nested_map_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#IF(#MAP1(0,1:2)>1)(Y,N)'), 'Y')
        self.assertEqual(writer.expand('#IF1(#MAP2(N,2:y),n)'), 'y')

    def test_macro_if_with_nested_peek_macro(self):
        writer = self._get_writer(snapshot=[10])
        self.assertEqual(writer.expand('#IF(#PEEK0>5)(>5,<=5)'), '>5')
        self.assertEqual(writer.expand('#IF0(#PEEK0,[#PEEK0])'), '[10]')

    def test_macro_if_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('IF')

        self._assert_error(writer, '#IF', "No valid expression found: '#IF'", prefix)
        self._assert_error(writer, '#IFx', "No valid expression found: '#IFx'", prefix)
        self._assert_error(writer, '#IF(0)', "No output strings: (0)", prefix)
        self._assert_error(writer, '#IF(0)(true,false,other)', "Too many output strings (expected 2): (0)(true,false,other)", prefix)
        self._assert_error(writer, '#IF1(true,false', "No closing bracket: (true,false", prefix)

    def test_macro_link_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('LINK')

        self._assert_error(writer, '#LINK', 'No parameters', prefix)
        self._assert_error(writer, '#LINK:', 'No page ID: #LINK:', prefix)
        self._assert_error(writer, '#LINK:(text)', 'No page ID: #LINK:(text)', prefix)
        self._assert_error(writer, '#LINK:(text', 'No closing bracket: (text', prefix)
        self._assert_error(writer, '#LINKpageID', 'Malformed macro: #LINKp...', prefix)
        self._assert_error(writer, '#LINK:Bugs', 'No link text: #LINK:Bugs', prefix)

        return writer, prefix

    def test_macro_map(self):
        writer = self._get_writer()

        # Key exists
        output = writer.expand('#MAP2(?,1:a,2:b,3:c)')
        self.assertEqual(output, 'b')

        # Key doesn't exist
        output = writer.expand('#MAP0(?,1:a,2:b,3:c)')
        self.assertEqual(output, '?')

        # Blank default and no keys
        output = writer.expand('#MAP1()')
        self.assertEqual(output, '')

        # No keys
        output = writer.expand('#MAP5(*)')
        self.assertEqual(output, '*')

        # Blank default value and no keys
        output = writer.expand('#MAP2()')
        self.assertEqual(output, '')

        # Key without value (defaults to key)
        output = writer.expand('#MAP7(0,1,7)')
        self.assertEqual(output, '7')

        # Arithmetic expression in 'value' parameter
        self.assertEqual(writer.expand('#MAP(2 * (2 + 1) + (11 - 3) / 2 - 4)(?,6:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(4**3)(?,64:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(5&3|4)(?,5:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(5^7)(?,2:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(4%3)(?,1:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(2<<2)(?,8:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP(4>>2)(?,1:OK)'), 'OK')

        # Arithmetic expression in mapping key
        self.assertEqual(writer.expand('#MAP6||?|(1 + 1) * 3 + (12 - 4) / 2 - 4:OK||'), 'OK')
        self.assertEqual(writer.expand('#MAP64(?,4**3:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP5(?,5&3|4:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP2(?,5^7:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP1(?,4%3:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP8(?,2<<2:OK)'), 'OK')
        self.assertEqual(writer.expand('#MAP1(?,4>>2:OK)'), 'OK')

        # Alternative delimiters
        for delim1, delim2 in (('[', ']'), ('{', '}')):
            output = writer.expand('#MAP1{}?,0:A,1:OK,2:C{}'.format(delim1, delim2))
            self.assertEqual(output, 'OK')

        # Alternative separator
        output = writer.expand('#MAP1|;?;0:A;1:Oh, OK;2:C;|')
        self.assertEqual(output, 'Oh, OK')

    def test_macro_map_with_nested_eval_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP#EVAL(1+1)(a,1:b,2:c)'), 'c')
        self.assertEqual(writer.expand('#MAP2(a,1:b,#EVAL(1+1):c)'), 'c')

    def test_macro_map_with_nested_for_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP(#FOR0,1(n,n,+))(a,1:b,2:c)'), 'b')
        self.assertEqual(writer.expand('#MAP2(a,1:b,#FOR1,2(n,n,*):c)'), 'c')
        self.assertEqual(writer.expand('#MAP2(?,#FOR0,2||n|n:n|,||)'), '2')

    def test_macro_map_with_nested_foreach_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP(#FOREACH(0,1)(n,n,+))(a,1:b,2:c)'), 'b')
        self.assertEqual(writer.expand('#MAP2(a,1:b,#FOREACH(1,2)(n,n,*):c)'), 'c')
        self.assertEqual(writer.expand('#MAP2(?,#FOREACH(0,1,2)||n|n:n|,||)'), '2')

    def test_macro_map_with_nested_if_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP#IF(1>2)(1,2)(a,1:b,2:c)'), 'c')
        self.assertEqual(writer.expand('#MAP1(a,#IF1(1,2):b,2:c)'), 'b')

    def test_macro_map_with_nested_map_macro(self):
        writer = self._get_writer()
        self.assertEqual(writer.expand('#MAP#MAP0(5,0:10,1:20)(,5:x,10:y,20:z)'), 'y')
        self.assertEqual(writer.expand('#MAP3(1,2:Y,#MAP8(3,7:Q):Z)'), 'Z')

    def test_macro_map_with_nested_peek_macro(self):
        writer = self._get_writer(snapshot=[23])
        self.assertEqual(writer.expand('#MAP#PEEK0(a,23:b,5:c)'), 'b')
        self.assertEqual(writer.expand('#MAP23(1,#PEEK0:2,5:3)'), '2')

    def test_macro_map_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('MAP')

        self._assert_error(writer, '#MAP', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#MAP0', "No mappings provided: 0", prefix)
        self._assert_error(writer, '#MAP0 ()', "No mappings provided: 0", prefix)
        self._assert_error(writer, '#MAP0(1,2:3', "No closing bracket: (1,2:3", prefix)
        self._assert_error(writer, '#MAP0(1,x1:3)', "Invalid key (x1): (1,x1:3)", prefix)

    def test_macro_peek(self):
        writer = self._get_writer(snapshot=(1, 2, 3))

        output = writer.expand('#PEEK0')
        self.assertEqual(output, '1')

        output = writer.expand('#PEEK($0001)')
        self.assertEqual(output, '2')

        # Arithmetic expression
        self.assertEqual(writer.expand('#PEEK($0001 + (5 + 3) / 2 - (14 - 2) / 3)'), '2')

        # Address is taken modulo 65536
        output = writer.expand('#PEEK65538')
        self.assertEqual(output, '3')

    def test_macro_peek_with_nested_eval_macro(self):
        writer = self._get_writer(snapshot=(1, 2))
        self.assertEqual(writer.expand('#PEEK#EVAL(0+1)'), '2')

    def test_macro_peek_with_nested_for_macro(self):
        writer = self._get_writer(snapshot=(1, 2))
        self.assertEqual(writer.expand('#PEEK(#FOR0,1(n,n,+))'), '2')

    def test_macro_peek_with_nested_foreach_macro(self):
        writer = self._get_writer(snapshot=(1, 2))
        self.assertEqual(writer.expand('#PEEK(#FOREACH(0,1)(n,n,+))'), '2')

    def test_macro_peek_with_nested_if_macro(self):
        writer = self._get_writer(snapshot=(1, 2))
        self.assertEqual(writer.expand('#PEEK#IF1(1,0)'), '2')

    def test_macro_peek_with_nested_map_macro(self):
        writer = self._get_writer(snapshot=(1, 2))
        self.assertEqual(writer.expand('#PEEK#MAP1(2,0:1,1:0)'), '1')

    def test_macro_peek_with_nested_peek_macro(self):
        writer = self._get_writer(snapshot=[1] * 258)
        writer.snapshot[257] = 101
        self.assertEqual(writer.expand('#PEEK(#PEEK0+256*#PEEK1)'), '101')

    def test_macro_peek_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('PEEK')

        self._assert_error(writer, '#PEEK', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#PEEK()', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#PEEK(3', "No closing bracket: (3", prefix)
        self._assert_error(writer, '#PEEK(4,5)', "Too many parameters (expected 1): '4,5'", prefix)

    def test_macro_poke_invalid(self):
        self._test_invalid_reference_macro('POKE')

    def test_macro_pokes(self):
        writer = self._get_writer(snapshot=[0] * 20)
        snapshot = writer.snapshot

        # addr, byte
        output = writer.expand('#POKES0,255')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[0], 255)

        # addr, byte, length
        output = writer.expand('#POKES0,254,10')
        self.assertEqual(output, '')
        self.assertEqual([254] * 10, snapshot[0:10])

        # addr, byte, length, step
        output = writer.expand('#POKES0,253,10,2')
        self.assertEqual(output, '')
        self.assertEqual([253] * 10, snapshot[0:20:2])

        # Two POKEs
        output = writer.expand('#POKES1,1;2,2')
        self.assertEqual(output, '')
        self.assertEqual([1, 2], snapshot[1:3])

        # Arithmetic expressions
        output = writer.expand('#POKES(1 + 1, 3 * 4, 10 - (1 + 1) * 2, (11 + 1) / 4)')
        self.assertEqual(output, '')
        self.assertEqual([12] * 6, snapshot[2:18:3])

    def test_macro_pokes_invalid(self):
        writer = self._get_writer(snapshot=[0])
        prefix = ERROR_PREFIX.format('POKES')

        self._assert_error(writer, '#POKES', 'No parameters (expected 2)', prefix)
        self._assert_error(writer, '#POKES0', "Not enough parameters (expected 2): '0'", prefix)
        self._assert_error(writer, '#POKES0,1;1', "Not enough parameters (expected 2): '1'", prefix)

    def test_macro_pops(self):
        writer = self._get_writer(snapshot=[0, 0])
        addr, byte = 1, 128
        writer.snapshot[addr] = byte
        writer.push_snapshot('test')
        writer.snapshot[addr] = (byte + 127) % 256
        output = writer.expand('#POPS')
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_pops_empty_stack(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('POPS')
        self._assert_error(writer, '#POPS', 'Cannot pop snapshot when snapshot stack is empty', prefix)

    def test_macro_pushs(self):
        writer = self._get_writer(snapshot=[0])
        addr, byte = 0, 64
        for name in ('test', '#foo', 'foo$abcd', ''):
            for suffix in ('', '(bar)', ':baz'):
                writer.snapshot[addr] = byte
                output = writer.expand('#PUSHS{}{}'.format(name, suffix))
                self.assertEqual(output, suffix)
                self.assertEqual(writer.snapshot[addr], byte)
                writer.snapshot[addr] = (byte + 127) % 256
                writer.pop_snapshot()
                self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_r_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('R')

        self._assert_error(writer, '#R', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#R@main', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#R#bar', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#R(baz)', "Cannot parse integer 'baz' in parameter string: 'baz'", prefix)
        self._assert_error(writer, '#R32768(qux', "No closing bracket: (qux", prefix)

        return writer, prefix

    def test_macro_refs_invalid(self):
        writer = self._get_writer(skool='')
        prefix = ERROR_PREFIX.format('REFS')

        self._assert_error(writer, '#REFS', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#REFSx', "No parameters (expected 1)", prefix)
        self._assert_error(writer, '#REFS34567(foo', "No closing bracket: (foo", prefix)
        self._assert_error(writer, '#REFS40000', "No entry at 40000", prefix)

    def test_macro_reg_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('REG')

        self._assert_error(writer, '#REG', 'Missing register argument', prefix)
        self._assert_error(writer, '#REGq', 'Bad register: "q"', prefix)
        self._assert_error(writer, "#REG'a", 'Bad register: "\'a"', prefix)
        self._assert_error(writer, "#REGxil", 'Bad register: "xil"', prefix)

    def test_macro_scr_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('SCR')

        self._test_invalid_image_macro(writer, '#SCR0,1,2,3,4,5,6,7,8', "Too many parameters (expected 7): '0,1,2,3,4,5,6,7,8'", prefix)
        self._test_invalid_image_macro(writer, '#SCR{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#SCR{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#SCR(foo', 'No closing bracket: (foo', prefix)

    def test_macro_space(self):
        writer = self._get_writer()
        space = '&#160;' if writer.needs_cwd() else ' '

        self.assertEqual(writer.expand('#SPACE'), space.strip())
        self.assertEqual(writer.expand('"#SPACE10"'), '"{}"'.format(space * 10))
        self.assertEqual(writer.expand('1#SPACE(7)1'), '1{}1'.format(space * 7))
        self.assertEqual(writer.expand('|#SPACE2+2|'), '|{}+2|'.format(space * 2))
        self.assertEqual(writer.expand('|#SPACE3-1|'), '|{}-1|'.format(space * 3))
        self.assertEqual(writer.expand('|#SPACE2*2|'), '|{}*2|'.format(space * 2))
        self.assertEqual(writer.expand('|#SPACE3/3|'), '|{}/3|'.format(space * 3))
        self.assertEqual(writer.expand('|#SPACE(1+3*2-10/2)|'), '|{}|'.format(space * 2))
        self.assertEqual(writer.expand('|#SPACE($01 + 3 * 2 - (7 + 3) / 2)|'), '|{}|'.format(space * 2))

    def test_macro_space_invalid(self):
        writer = self._get_writer()
        prefix = ERROR_PREFIX.format('SPACE')

        self._assert_error(writer, '#SPACE(2', "No closing bracket: (2", prefix)
        self._assert_error(writer, '#SPACE(5$3)', "Cannot parse integer '5$3' in parameter string: '5$3'", prefix)

    def test_macro_udg_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDG')

        self._test_invalid_image_macro(writer, '#UDG', 'No parameters (expected 1)', prefix)
        self._test_invalid_image_macro(writer, '#UDG(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0,1,2,3,4,5,6,7,8,9', "Too many parameters (expected 8): '0,1,2,3,4,5,6,7,8,9'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0:1,2,3', "Too many parameters (expected 2): '1,2,3'", prefix)
        self._test_invalid_image_macro(writer, '#UDG0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#UDG0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#UDG0(foo', 'No closing bracket: (foo', prefix)

    def test_macro_udgarray_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        self._test_invalid_image_macro(writer, '#UDGARRAY', 'No parameters (expected 1)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY(foo)', "Cannot parse integer 'foo' in parameter string: 'foo'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;(foo)', 'Expected UDG address range specification: #UDGARRAY1;', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0:(foo)', 'Expected mask address range specification: #UDGARRAY1;0:', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0', 'Missing filename: #UDGARRAY1;0', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0()', 'Missing filename: #UDGARRAY1;0()', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0}1(foo)', 'Missing filename: #UDGARRAY1;0{0,0}', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0(*)', 'Missing filename or frame ID: #UDGARRAY1;0(*)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;32768,1,2,3,4', "Too many parameters (expected 3): '1,2,3,4'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;32768:32769,1,2', "Too many parameters (expected 1): '1,2'", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;32768xJ', "Invalid multiplier in address range specification: 32768xJ", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0,23,14,5}(foo)', "Too many parameters in cropping specification (expected 4 at most): {0,0,23,14,5}", prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0{0,0,23,14(foo)', 'No closing brace on cropping specification: {0,0,23,14(foo)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY1;0(foo', 'No closing bracket: (foo', prefix)

    def test_macro_udgarray_frames_invalid(self):
        writer = self._get_writer(snapshot=[0] * 8)
        prefix = ERROR_PREFIX.format('UDGARRAY')

        self._test_invalid_image_macro(writer, '#UDGARRAY*(bar)', 'No frames specified: #UDGARRAY*(bar)', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo', 'Missing filename: #UDGARRAY*foo', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo()', 'Missing filename: #UDGARRAY*foo()', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo(bar', 'No closing bracket: (bar', prefix)
        self._test_invalid_image_macro(writer, '#UDGARRAY*foo,qux(bar)', "Missing 'delay' parameter for frame 'foo'", prefix)

        return writer, prefix
