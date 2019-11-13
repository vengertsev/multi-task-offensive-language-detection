import torch
from torch import nn
from transformers import BertForSequenceClassification, RobertaForSequenceClassification


class BERT(nn.Module):
    def __init__(self, model_size, num_labels=2):
        super(BERT, self).__init__()
        self.model = BertForSequenceClassification.from_pretrained(f'bert-{model_size}-uncased', num_labels=num_labels)

        # Freeze embeddings' parameters for saving memory
        for param in self.model.bert.embeddings.parameters():
            param.requires_grad = False

    def forward(self, inputs, mask, labels):
        outputs = self.model(inputs, attention_mask=mask, labels=labels)
        loss, logits = outputs[:2]
        # return loss, logits
        return logits

class RoBERTa(nn.Module):
    def __init__(self, model_size, num_labels=2):
        super(RoBERTa, self).__init__()
        self.model = RobertaForSequenceClassification.from_pretrained(f'roberta-{model_size}', num_labels=num_labels)

        # Freeze embeddings' parameters for saving memory
        for param in self.model.roberta.embeddings.parameters():
            param.requires_grad = False

    def forward(self, inputs, mask, labels):
        outputs = self.model(inputs, attention_mask=mask, labels=labels)
        loss, logits = outputs[:2]
        # return loss, logits
        return logits

class MTModel(nn.Module):
    def __init__(self, model, model_size):
        super(MTModel, self).__init__()
        if model == 'bert':
            pretrained = BertForSequenceClassification.from_pretrained(f'bert-{model_size}-uncased')
            self.main = pretrained.bert
            self.dropout = pretrained.dropout
        elif model == 'roberta':
            pretrained = RobertaForSequenceClassification.from_pretrained(f'roberta-{model_size}')
            self.main = pretrained.roberta
            self.dropout = pretrained.dropout

        # Freeze embeddings' parameters for saving memory
        for param in self.main.embeddings.parameters():
            param.requires_grad = False

        self.classifier_a = nn.Linear(in_features=768, out_features=2, bias=True)
        self.classifier_b = nn.Linear(in_features=768, out_features=3, bias=True)
        self.classifier_c = nn.Linear(in_features=768, out_features=4, bias=True)

    def forward(self, inputs, mask):
        outputs = self.main(inputs, attention_mask=mask)
        pooled_output = outputs[1]
        pooled_output = self.dropout(pooled_output)
        # logits for 3 sub-tasks
        logits_A = self.classifier_a(pooled_output)
        logits_B = self.classifier_b(pooled_output)
        logits_C = self.classifier_c(pooled_output)
        return logits_A, logits_B, logits_C


class GatedModel(nn.Module):
    def __init__(self, model, model_size):
        super(GatedModel, self).__init__()
        # using BERT/RoBERTa pre-trained model
        if model == 'bert':
            pretrainedA = BertForSequenceClassification.from_pretrained(f'bert-{model_size}-uncased')
            self.mainA = pretrainedA.bert
            pretrainedB = BertForSequenceClassification.from_pretrained(f'bert-{model_size}-uncased')
            self.mainB = pretrainedB.bert
            pretrainedC = BertForSequenceClassification.from_pretrained(f'bert-{model_size}-uncased')
            self.mainC = pretrainedC.bert
            
            # Freeze embeddings' parameters for saving memory
            for p in [
                # *self.model.robe
                *self.mainA.embeddings.word_embeddings.parameters(),
                *self.mainB.embeddings.word_embeddings.parameters(),
                *self.mainC.embeddings.word_embeddings.parameters(),
            ]:
                p.requires_grad=False
            
            self.dropoutA = pretrainedA.dropout
            self.dropoutB = pretrainedB.dropout
            self.dropoutC = pretrainedC.dropout
            if model_size == 'base':
                self.hidden_size = 768
            if model_size == 'large':
                self.hidden_size = 1024

            self.linearA = nn.Linear(in_features=self.hidden_size*3, out_features=self.hidden_size, bias=True)
            self.linearB = nn.Linear(in_features=self.hidden_size*3, out_features=self.hidden_size, bias=True)
            self.linearC = nn.Linear(in_features=self.hidden_size*3, out_features=self.hidden_size, bias=True)

            self.softmaxA = nn.Softmax(dim=1)
            self.softmaxB = nn.Softmax(dim=1)
            self.softmaxC = nn.Softmax(dim=1)
            
            self.classifier_a = nn.Linear(in_features=self.hidden_size, out_features=2, bias=True)
            self.classifier_b = nn.Linear(in_features=self.hidden_size, out_features=3, bias=True)
            self.classifier_c = nn.Linear(in_features=self.hidden_size, out_features=4, bias=True)

        elif model == 'roberta':
            pretrainedA = RobertaForSequenceClassification.from_pretrained(f'roberta-{model_size}')
            self.mainA = pretrainedA.roberta
            pretrainedB = RobertaForSequenceClassification.from_pretrained(f'roberta-{model_size}')
            self.mainB = pretrainedB.roberta
            pretrainedC = RobertaForSequenceClassification.from_pretrained(f'roberta-{model_size}')
            self.mainC = pretrainedC.roberta
            
            # Freeze embeddings' parameters for saving memory
            for p in [
                # *self.model.robe
                *self.mainA.embeddings.word_embeddings.parameters(),
                *self.mainB.embeddings.word_embeddings.parameters(),
                *self.mainC.embeddings.word_embeddings.parameters(),
            ]:
                p.requires_grad=False
            
            self.dropoutA = pretrainedA.classifier
            self.dropoutB = pretrainedB.classifier
            self.dropoutC = pretrainedC.classifier

            if model_size == 'base':
                self.hidden_size = 768
            if model_size == 'large':
                self.hidden_size = 1024

            self.linearA = nn.Linear(in_features=self.hidden_size*3, out_features=self.hidden_size, bias=True)
            self.linearB = nn.Linear(in_features=self.hidden_size*3, out_features=self.hidden_size, bias=True)
            self.linearC = nn.Linear(in_features=self.hidden_size*3, out_features=self.hidden_size, bias=True)

            self.softmaxA = nn.Softmax(dim=1)
            self.softmaxB = nn.Softmax(dim=1)
            self.softmaxC = nn.Softmax(dim=1)
            
            self.classifier_a = nn.Linear(in_features=self.hidden_size, out_features=2, bias=True)
            self.classifier_b = nn.Linear(in_features=self.hidden_size, out_features=3, bias=True)
            self.classifier_c = nn.Linear(in_features=self.hidden_size, out_features=4, bias=True)
            
    
    def forward(self, inputs, mask):
        outputsA = self.mainA(inputs, attention_mask=mask)
        pooled_outputA = outputsA[1]
        # pooled_outputA = self.dropoutA(pooled_outputA) # batch_size * hidden_size
        
        outputsB = self.mainB(inputs, attention_mask=mask)
        pooled_outputB = outputsB[1]
        # pooled_outputB = self.dropoutB(pooled_outputB) # batch_size * hidden_size
        
        outputsC = self.mainC(inputs, attention_mask=mask)
        pooled_outputC = outputsC[1]
        # pooled_outputC = self.dropoutC(pooled_outputC) # batch_size * hidden_size
        
        gateA = self.softmaxA(self.linearA(torch.cat((pooled_outputA, pooled_outputB, pooled_outputC), 1)))
        gateB = self.softmaxB(self.linearB(torch.cat((pooled_outputA, pooled_outputB, pooled_outputC), 1)))
        gateC = self.softmaxC(self.linearC(torch.cat((pooled_outputA, pooled_outputB, pooled_outputC), 1)))

        gateA_1 = torch.ones(gateA.shape).cuda() - gateA
        gateB_1 = torch.ones(gateB.shape).cuda() - gateB
        gateC_1 = torch.ones(gateC.shape).cuda() - gateC

        hidden_A = torch.mul(gateA_1, pooled_outputA) + torch.mul(torch.mul(gateA, 0.5), pooled_outputB) + torch.mul(torch.mul(gateA, 0.5), pooled_outputC)
        hidden_B = torch.mul(gateB_1, pooled_outputA) + torch.mul(torch.mul(gateB, 0.5), pooled_outputB) + torch.mul(torch.mul(gateB, 0.5), pooled_outputC)
        hidden_C = torch.mul(gateC_1, pooled_outputA) + torch.mul(torch.mul(gateC, 0.5), pooled_outputB) + torch.mul(torch.mul(gateC, 0.5), pooled_outputC)
        
        # logits for 3 sub-tasks
        logits_A = self.classifier_a(hidden_A)
        logits_B = self.classifier_b(hidden_B)
        logits_C = self.classifier_c(hidden_C)

        return logits_A, logits_B, logits_C
    
    
    
    