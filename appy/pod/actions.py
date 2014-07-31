# ------------------------------------------------------------------------------
# This file is part of Appy, a framework for building applications in the Python
# language. Copyright (C) 2007 Gaetan Delannay

# Appy is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.

# Appy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with
# Appy. If not, see <http://www.gnu.org/licenses/>.

# ------------------------------------------------------------------------------
from appy import Object
from appy.pod import PodError
from appy.pod.elements import *

# ------------------------------------------------------------------------------
EVAL_ERROR = 'Error while evaluating expression "%s". %s'
FROM_EVAL_ERROR = 'Error while evaluating the expression "%s" defined in the ' \
                  '"from" part of a statement. %s'
WRONG_SEQ_TYPE = 'Expression "%s" is not iterable.'
TABLE_NOT_ONE_CELL = "The table you wanted to populate with '%s' " \
                     "can\'t be dumped with the '-' option because it has " \
                     "more than one cell in it."

# ------------------------------------------------------------------------------
class BufferAction:
    '''Abstract class representing a action (=statement) that must be performed
       on the content of a buffer (if, for...).'''
    def __init__(self, name, buffer, expr, elem, minus, source, fromExpr):
        self.name = name # Actions may be named. Currently, the name of an
        # action is only used for giving a name to "if" actions; thanks to this
        # name, "else" actions that are far away may reference their "if".
        self.buffer = buffer # The object of the action
        self.expr = expr # Python expression to evaluate (may be None in the
        # case of a NullAction or ElseAction, for example)
        self.elem = elem # The element within the buffer that is the object
        # of the action.
        self.minus = minus # If True, the main elem(s) must not be dumped.
        self.source = source # If 'buffer', we must dump the (evaluated) buffer
        # content. If 'from', we must dump what comes from the 'from' part of
        # the action (='fromExpr')
        self.fromExpr = fromExpr
        # When an error occurs, must we raise it or write it into the buffer?
        self.raiseErrors = not self.buffer.pod
        # Several actions may co-exist for the same buffer, as a chain of
        # BufferAction instances, defined via the following attribute.
        self.subAction = None

    def getExceptionLine(self, e):
        '''Gets the line describing exception p_e, containing the pathname of
           the exception class, the exception's message and line number.'''
        # https://bugs.launchpad.net/appy/+bug/1244738
        #return '%s.%s: %s' % (e.__module__, e.__class__.__name__, str(e))
        return '%s: %s' % (e.__class__.__name__, str(e))

    def manageError(self, result, context, errorMessage, dumpTb=True):
        '''Manage the encountered error: dump it into the buffer or raise an
           exception if self.raiseErrors is True.'''
        if self.raiseErrors:
            if not self.buffer.pod:
                # Add in the error message the line nb where the errors occurs
                # within the PX.
                locator = self.buffer.env.parser.locator
                # The column number may not be given.
                col = locator.getColumnNumber()
                if col == None: col = ''
                else: col = ', column %d' % col
                errorMessage += ' (line %s%s)' % (locator.getLineNumber(), col)
            raise Exception(errorMessage)
        # Empty the buffer (pod-only)
        self.buffer.__init__(self.buffer.env, self.buffer.parent)
        PodError.dump(self.buffer, errorMessage, withinElement=self.elem,
                      dumpTb=dumpTb)
        self.buffer.evaluate(result, context)

    def evaluateExpression(self, result, context, expr):
        '''Evaluates expression p_expr with the current p_context. Returns a
           tuple (result, errorOccurred).'''
        try:
            res = eval(expr, context)
            error = False
        except Exception, e:
            res = None
            errorMessage = EVAL_ERROR % (expr, self.getExceptionLine(e))
            self.manageError(result, context, errorMessage)
            error = True
        return res, error

    def execute(self, result, context):
        '''Executes this action given some p_context and add the result to
           p_result.'''
        # Check that if minus is set, we have an element which can accept it
        if self.minus and isinstance(self.elem, Table) and \
           (not self.elem.tableInfo.isOneCell()):
            self.manageError(result, context, TABLE_NOT_ONE_CELL % self.expr)
        else:
            error = False
            # Evaluate self.expr in eRes.
            eRes = None
            if self.expr:
                eRes,error = self.evaluateExpression(result, context, self.expr)
            if not error:
                # Trigger action-specific behaviour.
                self.do(result, context, eRes)

    def evaluateBuffer(self, result, context):
        if self.source == 'buffer':
            self.buffer.evaluate(result, context, removeMainElems=self.minus)
        else:
            # Evaluate self.fromExpr in feRes.
            feRes = None
            error = False
            try:
                feRes = eval(self.fromExpr, context)
            except Exception, e:
                msg = FROM_EVAL_ERROR% (self.fromExpr, self.getExceptionLine(e))
                self.manageError(result, context, msg, dumpTb=False)
                error = True
            if not error:
                result.write(feRes)

    def addSubAction(self, action):
        '''Adds p_action as a sub-action of this action.'''
        if not self.subAction:
            self.subAction = action
        else:
            self.subAction.addSubAction(action)

class IfAction(BufferAction):
    '''Action that determines if we must include the content of the buffer in
       the result or not.'''
    def do(self, result, context, exprRes):
        if exprRes:
            if self.subAction:
                self.subAction.execute(result, context)
            else:
                self.evaluateBuffer(result, context)
        else:
            if self.buffer.isMainElement(Cell.OD):
                # Don't leave the current row with a wrong number of cells
                result.dumpElement(Cell.OD.elem)

class ElseAction(IfAction):
    '''Action that is linked to a previous "if" action. In fact, an "else"
       action works exactly like an "if" action, excepted that instead of
       defining a conditional expression, it is based on the negation of the
       conditional expression of the last defined "if" action.'''

    def __init__(self, name, buff, expr, elem, minus, src, fromExpr, ifAction):
        IfAction.__init__(self, name, buff, None, elem, minus, src, fromExpr)
        self.ifAction = ifAction

    def do(self, result, context, exprRes):
        # This action is executed if the tied "if" action is not executed.
        ifAction = self.ifAction
        iRes,error = ifAction.evaluateExpression(result, context, ifAction.expr)
        IfAction.do(self, result, context, not iRes)

class ForAction(BufferAction):
    '''Actions that will include the content of the buffer as many times as
       specified by the action parameters.'''

    def __init__(self, name, buff, expr, elem, minus, iter, src, fromExpr):
        BufferAction.__init__(self, name, buff, expr, elem, minus, src,fromExpr)
        self.iter = iter # Name of the iterator variable used in the each loop

    def initialiseLoop(self, context, elems):
        '''Initialises information about the loop, before entering into it.'''
        # The "loop" object, made available in the POD context, contains info
        # about all currently walked loops. For every walked loop, a specific
        # object, le'ts name it curLoop, accessible at getattr(loop, self.iter),
        # stores info about its status:
        #   * curLoop.length  gives the total number of walked elements withhin
        #                     the loop
        #   * curLoop.nb      gives the index (starting at 0) if the currently
        #                     walked element.
        #   * curLoop.first   is True if the currently walked element is the
        #                     first one.
        #   * curLoop.last    is True if the currently walked element is the
        #                     last one.
        #   * curLoop.odd     is True if the currently walked element is odd
        #   * curLoop.even    is True if the currently walked element is even
        # For example, if you have a "for" statement like this:
        #        for elem in myListOfElements
        # Within the part of the ODT document impacted by this statement, you
        # may access to:
        #   * loop.elem.length to know the total length of myListOfElements
        #   * loop.elem.nb     to know the index of the current elem within
        #                      myListOfElements.
        if 'loop' not in context:
            context['loop'] = Object()
        try:
            total = len(elems)
        except:
            total = 0
        curLoop = Object(length=total)
        setattr(context['loop'], self.iter, curLoop)
        return curLoop

    def do(self, result, context, elems):
        '''Performs the "for" action. p_elems is the list of elements to
           walk, evaluated from self.expr.'''
        # Check p_exprRes type.
        try:
            # All "iterable" objects are OK.
            str(elems)
        except TypeError:
            self.manageError(result, context, WRONG_SEQ_TYPE % self.expr)
            return
        # Remember variable hidden by iter if any
        hasHiddenVariable = False
        if context.has_key(self.iter):
            hiddenVariable = context[self.iter]
            hasHiddenVariable = True
        # In the case of cells, initialize some values
        isCell = False
        if isinstance(self.elem, Cell):
            isCell = True
            nbOfColumns = self.elem.tableInfo.nbOfColumns
            initialColIndex = self.elem.colIndex
            currentColIndex = initialColIndex
            rowAttributes = self.elem.tableInfo.curRowAttrs
            # If p_elems is empty, dump an empty cell to avoid having the wrong
            # number of cells for the current row.
            if not elems:
                result.dumpElement(Cell.OD.elem)
        # Enter the "for" loop.
        loop = self.initialiseLoop(context, elems)
        i = -1
        for item in elems:
            i += 1
            loop.nb = i
            loop.first = i == 0
            loop.last = i == (loop.length-1)
            loop.even = (i%2)==0
            loop.odd = not loop.even
            context[self.iter] = item
            # Cell: add a new row if we are at the end of a row
            if isCell and (currentColIndex == nbOfColumns):
                result.dumpEndElement(Row.OD.elem)
                result.dumpStartElement(Row.OD.elem, rowAttributes)
                currentColIndex = 0
            # If a sub-action is defined, execute it.
            if self.subAction:
                self.subAction.execute(result, context)
            else:
                # Evaluate the buffer directly.
                self.evaluateBuffer(result, context)
            # Cell: increment the current column index
            if isCell:
                currentColIndex += 1
        # Cell: leave the last row with the correct number of cells
        if isCell and elems and False:
            wrongNbOfCells = (currentColIndex-1) - initialColIndex
            if wrongNbOfCells < 0: # Too few cells for last row
                for i in range(abs(wrongNbOfCells)):
                    context[self.iter] = ''
                    self.buffer.evaluate(result, context, subElements=False)
                    # This way, the cell is dumped with the correct styles
            elif wrongNbOfCells > 0: # Too many cells for last row
                # Finish current row
                nbOfMissingCells = 0
                if currentColIndex < nbOfColumns:
                    nbOfMissingCells = nbOfColumns - currentColIndex
                    context[self.iter] = ''
                    for i in range(nbOfMissingCells):
                        self.buffer.evaluate(result, context, subElements=False)
                result.dumpEndElement(Row.OD.elem)
                # Create additional row with remaining cells
                result.dumpStartElement(Row.OD.elem, rowAttributes)
                nbOfRemainingCells = wrongNbOfCells + nbOfMissingCells
                nbOfMissingCellsLastLine = nbOfColumns - nbOfRemainingCells
                context[self.iter] = ''
                for i in range(nbOfMissingCellsLastLine):
                    self.buffer.evaluate(result, context, subElements=False)
        # Delete the object representing info about the current loop.
        try:
            delattr(context['loop'], self.iter)
        except AttributeError:
            pass
        # Restore hidden variable if any
        if hasHiddenVariable:
            context[self.iter] = hiddenVariable
        else:
            if elems:
                if self.iter in context: # May not be the case on error.
                    del context[self.iter]

class NullAction(BufferAction):
    '''Action that does nothing. Used in conjunction with a "from" clause, it
       allows to insert in a buffer arbitrary odt content.'''
    def do(self, result, context, exprRes):
        self.evaluateBuffer(result, context)

class VariablesAction(BufferAction):
    '''Action that allows to define a set of variables somewhere in the
       template.'''
    def __init__(self, name, buff, elem, minus, variables, src, fromExpr):
        # We do not use the default Buffer.expr attribute for storing the Python
        # expression, because here we will have several expressions, one for
        # every defined variable.
        BufferAction.__init__(self,name, buff, None, elem, minus, src, fromExpr)
        # Definitions of variables: ~[(s_name, s_expr)]~
        self.variables = variables

    def do(self, result, context, exprRes):
        '''Evaluate the variables' expressions: because there are several
           expressions, we do not use the standard, single-expression-minded
           BufferAction code for evaluating our expressions.

           We remember the names and values of the variables that we will hide
           in the context: after execution of this buffer we will restore those
           values.
        '''
        hidden = None
        for name, expr in self.variables:
            # Evaluate variable expression in vRes.
            vRes, error = self.evaluateExpression(result, context, expr)
            if error: return
            # Remember the variable previous value if already in the context
            if name in context:
                if not hidden:
                    hidden = {name: context[name]}
                else:
                    hidden[name] = context[name]
            # Store the result into the context
            context[name] = vRes
        # If a sub-action is defined, execute it.
        if self.subAction:
            self.subAction.execute(result, context)
        else:
            # Evaluate the buffer directly.
            self.evaluateBuffer(result, context)
        # Restore hidden variables if any
        if hidden: context.update(hidden)
        # Delete not-hidden variables
        for name, expr in self.variables:
            if hidden and (name in hidden): continue
            del context[name]
# ------------------------------------------------------------------------------
