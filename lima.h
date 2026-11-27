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

#ifndef LIMAANALYZER_H
#define LIMAANALYZER_H

#include "macros.h"
#include "Doc.h"

#include <memory>
#include <string>
#include <vector>


class LimaAnalyzerPrivate;
class BINDINGS_API LimaAnalyzer
{
  friend class LimaAnalyzerPrivate;
public:
  LimaAnalyzer(const std::string& langs,
               const std::string& pipelines,
               const std::string& modulePath,
               const std::string& user_config_path="",
               const std::string& user_resources_path="",
               const std::string& meta="");

  ~LimaAnalyzer();
  LimaAnalyzer(const LimaAnalyzer& a) ;
  LimaAnalyzer& operator=(const LimaAnalyzer& a) ;

  std::string analyzeText(const std::string& text,
                          const std::string& lang="",
                          const std::string& pipeline="",
                          const std::string& meta="") const;
  Doc operator()(
    const std::string& text,
                 const std::string& lang="",
                 const std::string& pipeline="",
                 const std::string& meta="");

  bool addPipelineUnit(const std::string& pipeline,
                       const std::string& media,
                       const std::string& jsonGroupString);

  /** Adds to the resources of the media the one defined by the group json
   * string, as in addPipelineUnit (e.g. {"name": "MyRules", "class":
   * "AutomatonRecognizer", "rules": ""}). It is created when first used. A
   * resource of the same name must not exist. */
  bool addResource(const std::string& media,
                   const std::string& jsonGroupString);

  /** Adds to the process units of the media the one defined by the group
   * json string, as in addPipelineUnit. It is created when first used by a
   * pipeline (see addPipeline). A unit of the same name must not exist. A
   * ProcessUnitPipeline lists its units in a "processUnitSequence" list. */
  bool addProcessUnit(const std::string& media,
                      const std::string& jsonGroupString);

  /** Declares the pipeline of the media made of the process unit named unit
   * (a ProcessUnitPipeline, of the configuration or added by
   * addProcessUnit). The units it shares with other pipelines (and their
   * models) are not created again. */
  bool addPipeline(const std::string& pipeline,
                   const std::string& media,
                   const std::string& unit);

  /** Declares the named entity type group.type (and the group if needed),
   * e.g. for the rules given to setRecognizerRules. */
  bool addEntityType(const std::string& group, const std::string& type);

  /** Replaces the rules of the recognizer resource (class
   * AutomatonRecognizer) of the media by the ModEx rules of the given file
   * (text format, utf-8), compiled. The process units using the recognizer
   * use the new rules from the next analysis. */
  bool setRecognizerRules(const std::string& media,
                          const std::string& recognizer,
                          const std::string& rulesFile);

  /** return true if an error occured */
  bool error();
  /** return the error message if an error occured and reset the error state */
  std::string errorMessage();

private:
  LimaAnalyzerPrivate* m_d;
};

#endif // LIMAANALYZER_H
