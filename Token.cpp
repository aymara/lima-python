// Copyright 2019-2022 CEA LIST
// SPDX-FileCopyrightText: 2019-2022 CEA LIST <gael.de-chalendar@cea.fr>
//
// SPDX-License-Identifier: MIT

/****************************************************************************
**
** Copyright (C) 2018 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the Qt for Python examples of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:BSD$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** BSD License Usage
** Alternatively, you may use this file under the terms of the BSD license
** as follows:
**
** "Redistribution and use in source and binary forms, with or without
** modification, are permitted provided that the following conditions are
** met:
**   * Redistributions of source code must retain the above copyright
**     notice, this list of conditions and the following disclaimer.
**   * Redistributions in binary form must reproduce the above copyright
**     notice, this list of conditions and the following disclaimer in
**     the documentation and/or other materials provided with the
**     distribution.
**   * Neither the name of The Qt Company Ltd nor the names of its
**     contributors may be used to endorse or promote products derived
**     from this software without specific prior written permission.
**
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
**
** $QT_END_LICENSE$
**
****************************************************************************/

#include "Token.h"

#include <iostream>

class TokenPrivate
{
  friend class Token;

  TokenPrivate();
  ~TokenPrivate() = default;
  TokenPrivate(const Token& a) = delete;
  Token& operator=(const Token& a) = delete;

  int len;
  std::string text;
  std::string lemma;
  int i;
  int pos;
  std::string tag;
  std::string dep;
};


TokenPrivate::TokenPrivate()
{
}

Token::Token()
{
  m_d = new TokenPrivate();
}

Token::Token(int len,
      const std::string& text,
      const std::string& lemma,
      int i,
      int pos,
      const std::string& tag,
      const std::string& dep)
{
  m_d = new TokenPrivate();
  m_d->len = len;
  m_d->text = text;
  m_d->lemma = lemma;
  m_d->i = i;
  m_d->pos = pos;
  m_d->tag = tag;
  m_d->dep = dep;

}


Token::~Token()
{
  delete m_d;
}

Token::Token(const Token& a) : m_d(new TokenPrivate())
{
  std::cerr << "Token::Token copy constructor" << std::endl;
}

Token& Token::operator=(const Token& a)
{
  std::cerr << "Token::operator=" << std::endl;
  delete m_d;
  m_d = new TokenPrivate();
  return *this;
}

int Token::len()
{
  return m_d->len;
}
std::string Token::text()
{
  return m_d->text;
}

// std::vector<Token> Token::children()
// Doc& Token::doc()
// Token Token::head()
int Token::i()
{
  return m_d->i;
}

std::string Token::lemma()
{
  return m_d->lemma;
}

int Token::pos()
{
  return m_d->pos;
}

std::string Token::tag()
{
  return m_d->tag;
}

std::string Token::dep()
{
  return m_d->dep;
}

