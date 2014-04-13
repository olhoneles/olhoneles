# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Marcelo Jorge Vieira <metal@alucinados.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django import forms
from parsley.decorators import parsleyfy
from captcha.fields import ReCaptchaField


@parsleyfy
class ContactUsForm(forms.Form):

    name = forms.CharField(
        label="Nome",
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Seu nome",
                   "data-trigger": "change",
                   "class": "span5"}))

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Seu email",
                   "data-trigger": "change",
                   "class": "span5"}))

    message = forms.CharField(
        label="Mensagem",
        required=True,
        widget=forms.Textarea(
            attrs={"placeholder": "Sua mensagem",
                   "data-trigger": "change",
                   "class": "span5",
                   'rows': 5}))

    captcha = ReCaptchaField(attrs={'theme' : 'clean'})

