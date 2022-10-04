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

#include "Doc.h"
#include "Doc_private.h"
#include "Token.h"

#include "common/MediaticData/mediaticData.h"
#include <common/ProcessUnitFramework/AnalysisContent.h>
#include <linguisticProcessing/common/linguisticData/LimaStringText.h>
#include <linguisticProcessing/core/LinguisticAnalysisStructure/AnalysisGraph.h>

#include <iostream>
#include <vector>

using namespace Lima::LinguisticProcessing;
using MedData = Lima::Common::MediaticData::MediaticData ;


Doc::Doc(bool error, const std::string& errorMessage)
{
  m_d = new DocPrivate();
  m_d->error = error;
  m_d->errorMessage = errorMessage;
}

Doc::~Doc()
{
  delete m_d;
}

Doc::Doc(const Doc& a) : m_d(new DocPrivate(*a.m_d))
{
  // std::cerr << "Doc::Doc copy constructor" << std::endl;
}

Doc& Doc::operator=(const Doc& a)
{
  // std::cerr << "Doc::operator=" << std::endl;
  *m_d = *a.m_d;
  return *this;
}

bool Doc::error() const
{
  return m_d->error;
}

std::string Doc::errorMessage() const
{
  return m_d->errorMessage;
}

Token& Doc::operator[](int i)
{
  return m_d->tokens[i];
}

Token& Doc::at(int i)
{
  return m_d->tokens[i];
}

int Doc::len()
{
  return m_d->tokens.size();
}

std::string Doc::text()
{
  auto originalText = static_cast<LimaStringText*>(m_d->analysis->getData("Text"));

  return originalText->toStdString();
}

const std::vector<Span>& Doc::sentences() const
{
  return m_d->sentences;
}

const std::string& Doc::language() const
{
  return m_d->language;
}
